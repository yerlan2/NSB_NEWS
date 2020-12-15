import numpy as np
import pandas as pd

import pyspark
from pyspark.sql.session import SparkSession
from pyspark.sql.functions import concat_ws
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.feature import RegexTokenizer, StopWordsRemover, Word2Vec

import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

nltk.download('stopwords')
STOP_WORDS = list(set(stopwords.words('english')).union(set(ENGLISH_STOP_WORDS)))

spark = SparkSession.builder.appName('NSB news').getOrCreate()
sc = spark.sparkContext

# Calculate cosine similarity between two vectors 
def cosine_sim(v1, v2):
    return float( np.dot(v1, v2) / np.sqrt(np.dot(v1, v1)) / np.sqrt(np.dot(v2, v2)) )

def content_recommend(article_ids, articles):
    article_vecs = np.array(articles.select('vector')\
        .filter( articles.id.isin(*article_ids) ).collect())[:, 0]
    articles = articles.select('id', 'vector').collect()
    recommended_ids = []
    for i, article_id in enumerate(article_ids):
        t = sc.parallelize( (id_vec[0], cosine_sim(article_vecs[i], id_vec[1])) for id_vec in articles )
        similarity = spark.createDataFrame(t)\
            .withColumnRenamed('_1', 'id')\
            .withColumnRenamed('_2', 'similarity')
        similarity = similarity\
            .filter(~similarity.id.isin(*article_ids))\
            .orderBy('similarity', ascending = False)\
            .limit(8)
        recommended_ids.extend(similarity.select('id').rdd.map(lambda row: row[0]).collect())
    
    return recommended_ids

def transform(data):
    tokenizer = RegexTokenizer(inputCol="text", outputCol="words", pattern="\\W")
    data = tokenizer.transform(data)
    remover = StopWordsRemover(inputCol='words', outputCol='filteredWords', stopWords=STOP_WORDS)
    data = remover.transform(data)
    word2vec = Word2Vec(vectorSize=100, minCount=5, inputCol='filteredWords', outputCol='vector', seed=42)
    articles = word2vec.fit(data).transform(data)
    return articles

def get_recommendations(articles_ids, df):
    df = spark.createDataFrame(df)
    df = df.select('id', 'title', 'description', 'content').dropna()
    df = df.withColumn('text', concat_ws(' ', df.title, df.description, df.content))\
        .drop('title')\
        .drop('description')\
        .drop('content')
    data = df
    articles = transform(data)
    recommendations = content_recommend(articles_ids, articles)
    return recommendations

