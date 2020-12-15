"""
import pandas as pd

data = pd.read_csv('news_with_labels_cleaned.csv')
del data['Unnamed: 0']

data = data.drop_duplicates(subset=['title'], keep='first')
print(data)
data.to_csv('news.csv')
"""
 

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

db  = sqlite3.connect('news.db')
cur = db.cursor()

data = pd.read_csv('news.csv')
del data['Unnamed: 0']
data = data.replace(np.nan, '')


source_name = data['source.name'].drop_duplicates(keep='first')
sql_insert_into = 'INSERT INTO sources(name) VALUES(?)'
for x in source_name.values.tolist():
    cur.execute(sql_insert_into, [x])


category = data['category'].drop_duplicates(keep='first')
sql_insert_into = 'INSERT INTO categories(name) VALUES(?)'
for x in category.values.tolist():
    cur.execute(sql_insert_into, [x])


sql_insert_into_articles = 'INSERT INTO articles(source_id, category_id, author, title, description, url, urlToImage, publishedAt, content) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)'
for i in range(len(data)):
    cur.execute("SELECT id FROM sources WHERE name=?", [data['source.name'][i]])
    source_id, = cur.fetchone()
    cur.execute("SELECT id FROM categories WHERE name=?", [data['category'][i]])
    category_id, = cur.fetchone()
    
    cur.execute(sql_insert_into_articles, [
        source_id, category_id, 
        data['author'][i], 
        data['title'][i], 
        data['description'][i], 
        data['url'][i], 
        data['urlToImage'][i], 
        datetime.strptime(data['publishedAt'][i],"%Y-%m-%dT%H:%M:%SZ"), 
        data['content'][i],
    ])


db.commit()

