import re
import pickle
import string
import tensorflow as tf
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization

def custom_standardization(input_data):
    lowercase = tf.strings.lower(input_data)
    std_text = tf.strings.regex_replace(lowercase, '[%s]' % re.escape(string.punctuation), '')
    return std_text

def vectorize_sentence(text, restored_vectorizer):
    text = tf.expand_dims(text, -1)
    return restored_vectorizer(text)

def loadVectorizer():
    vectorizer_path = './category/vectorizer/vectorizer.sav'
    from_disk = pickle.load(open(vectorizer_path, 'rb'))
    restored_vectorizer = TextVectorization.from_config(from_disk['config'])

    # You have to call `adapt` with some dummy data (BUG in Keras)
    restored_vectorizer.adapt(tf.data.Dataset.from_tensor_slices(['dummy']))
    restored_vectorizer.set_weights(from_disk['weights'])

    return restored_vectorizer

def loadKeras():
    keras_model_path = './category/keras'
    return tf.keras.models.load_model(keras_model_path)

def getMappedLabel(pred):
    labels = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
    labels_map = dict(enumerate(labels))
    pred = pred.argmax(axis=1)[0]
    return labels_map[pred]

def predict_category(new_data):
    restored_vectorizer = loadVectorizer()
    restored_keras_model = loadKeras()
    new_data = vectorize_sentence(new_data, restored_vectorizer)
    pred = restored_keras_model.predict(new_data)
    return getMappedLabel(pred)