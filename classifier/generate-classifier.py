"""
Note: needs the questions.json file in the same directory as this file.
It should contain all of the questions in the database dumped from mongodb.
"""

import json

def hhi(arr):
    return sum([_**2 for _ in arr]) / sum(arr) ** 2


def normalized_hhi(arr):
    return (hhi(arr) - 1/len(arr)) / (1 - 1/len(arr))


def removePunctuation(s, punctuation='''.,!-;:'"\/?@#$%^&*_~()[]{}“”‘’'''):
    return ''.join(ch for ch in s if ch not in punctuation)


questions = open('questions.json')
with open('../stop-words.txt') as f:
    stop_words = set(f.readlines())
    stop_words = set([word.strip() for word in stop_words])

with open('../subcategories.txt') as f:
    SUBCATEGORIES = [line.strip() for line in f.readlines()]

word_to_subcat = {}

for line in questions:
    data = json.loads(line)
    if 'subcategory' not in data: continue

    subcategory = data['subcategory']

    if subcategory not in SUBCATEGORIES: continue
    subcategory_index = SUBCATEGORIES.index(subcategory)

    if data['type'] == 'tossup':
        tokens = removePunctuation(data['question']).lower().split()
    if data['type'] == 'bonus' and 'parts' in data and len(data['parts']) == 3:
        tokens = removePunctuation(data['leadin'] + ' ' + data['parts'][0] + data['parts'][1] + data['parts'][2]).lower().split()

    tokens = [token for token in tokens if token not in stop_words]
    for token in tokens:
        if token not in word_to_subcat:
            word_to_subcat[token] = [0 for _ in range(len(SUBCATEGORIES))]

        word_to_subcat[token][subcategory_index] += 1

with open('word_to_subcat.json', 'w') as f:
    json.dump(word_to_subcat, f)

for word in word_to_subcat:
    factor = normalized_hhi(word_to_subcat[word])**4 / sum(word_to_subcat[word])
    word_to_subcat[word] = [factor * i for i in word_to_subcat[word]]

with open('word_to_subcat_normalized.json', 'w') as f:
    json.dump(word_to_subcat, f)