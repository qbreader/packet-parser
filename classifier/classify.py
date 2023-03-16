import json
import math
import numpy as np
import os

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(CURRENT_PATH, 'stop-words.txt')) as f:
    STOP_WORDS = set(f.readlines())
    STOP_WORDS = set([word.strip() for word in STOP_WORDS])

with open(os.path.join(CURRENT_PATH, 'subcategories.txt')) as f:
    SUBCATEGORIES = [line.strip() for line in f.readlines()]

with open(os.path.join(CURRENT_PATH, 'word-to-subcat.json')) as f:
    WORD_TO_SUBCAT_PROBABILITY = json.load(f)

with open(os.path.join(CURRENT_PATH, '../subcat-to-cat.json')) as f:
    SUBCAT_TO_CAT = json.load(f)


def classify_question(question, type='tossup'):
    if type == 'tossup':
        prediction = classify_subcategory(question['question'] + ' ' + question['answer'])
    elif type == 'bonus':
        prediction = classify_subcategory(
            question['leadin'] + ' ' + ' '.join(question['parts']) + ' '.join(question['answers'])
        )
    else:
        raise ValueError('type must be tossup or bonus')

    return SUBCAT_TO_CAT[prediction], prediction


def classify_subcategory(text, EPSILON=0.00001):
    likelihoods = [0 for _ in SUBCATEGORIES]
    text = removePunctuation(text).lower().split()
    for token in text:
        if token in STOP_WORDS:
            continue

        if token in WORD_TO_SUBCAT_PROBABILITY:
            for i in range(len(SUBCATEGORIES)):
                likelihoods[i] += math.log(WORD_TO_SUBCAT_PROBABILITY[token][i] + EPSILON)
        else:
            # print('Token not in word-to-subcat:', token)
            pass

    max_likelihood = max(likelihoods)
    # as far as I can tell, there's always only one valid index
    valid_indices = [i for i, likelihood in enumerate(likelihoods) if likelihood == max_likelihood]
    return SUBCATEGORIES[np.random.choice(valid_indices)]


def removePunctuation(s, punctuation='''.,!-;:'"\/?@#$%^&*_~()[]{}“”‘’'''):
    return ''.join(ch for ch in s if ch not in punctuation)


if __name__ == '__main__':
    for line in open('input.txt'):
        data = json.loads(line.strip())
        prediction = classify_subcategory(data['text'])
        cat, subcat = SUBCAT_TO_CAT[prediction], prediction
        data['category'] = cat
        data['subcategory'] = subcat
        print(json.dumps(data, indent=None))
