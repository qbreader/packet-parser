"""
Note: needs the questions.json file in the same directory as this file.
It should contain all of the questions in the database dumped from mongodb.
"""

from collections import Counter
import json
from math import log
from nltk.stem import PorterStemmer
from tqdm import tqdm

def removePunctuation(s, punctuation='''.,!-;:'"\/?@#$%^&*_~()[]{}“”‘’'''):
    return ''.join(ch for ch in s if ch not in punctuation)

def predict(text, naive_bayes_data):
    text = removePunctuation(text).lower().split()
    tokens = [token for token in text if token not in stop_words]
    tokens = [ps.stem(token) for token in tokens]
    token_counter = Counter(tokens)
    probs = {subcat: 0 for subcat in SUBCATEGORIES}

    for subcat in SUBCATEGORIES:
        for token in token_counter:
            # skip tokens that we don't have data for
            if token in naive_bayes_data and token_counter[token] in naive_bayes_data[token][subcat]:
                probs[subcat] += log(naive_bayes_data[subcat][token][token_counter[token]])

    best_subcat = max(probs)


ps = PorterStemmer()

questions = open('questions.json')
questions = questions.readlines()
questions = questions[int(0.2*len(questions)):]

with open('../stop-words.txt') as f:
    stop_words = set(f.readlines())
    stop_words = set([word.strip() for word in stop_words])

with open('../subcategories.txt') as f:
    SUBCATEGORIES = [line.strip() for line in f.readlines()]

naive_bayes_data = {}
class_priors = {0 for subcat in SUBCATEGORIES}

for line in tqdm(questions):
    data = json.loads(line)
    if 'subcategory' not in data: continue

    subcategory = data['subcategory']

    if subcategory not in SUBCATEGORIES: continue

    if data['type'] == 'tossup':
        tokens = removePunctuation(data['question']).lower().split()
    if data['type'] == 'bonus' and 'parts' in data and len(data['parts']) == 3:
        tokens = removePunctuation(data['leadin'] + ' ' + data['parts'][0] + data['parts'][1] + data['parts'][2]).lower().split()

    tokens = [token for token in tokens if token not in stop_words]
    tokens = [ps.stem(token) for token in tokens]
    token_counter = Counter(tokens)

    for token in tokens:
        if token not in naive_bayes_data:
            naive_bayes_data[token] = {subcat: {} for subcat in SUBCATEGORIES}

        naive_bayes_data[token][subcategory][token_counter[token]] = naive_bayes_data[token][subcategory].get(token_counter[token], 0) + 1
