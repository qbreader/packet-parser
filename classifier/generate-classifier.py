"""
Note: needs the questions.json file in the same directory as this file.
It should contain all of the questions in the database dumped from mongodb.
"""

import json
import math
import numpy as np
from tqdm import tqdm

np.random.seed(0)

questions = open("tossups.json").readlines() + open("bonuses.json").readlines()
np.random.shuffle(questions)
print("Number of questions:", len(questions))


def hhi(arr):
    return sum([_**2 for _ in arr]) / sum(arr) ** 2


def normalized_hhi(arr):
    return (hhi(arr) - 1 / len(arr)) / (1 - 1 / len(arr))


def removePunctuation(s, punctuation=""".,!-;:'"\/?@#$%^&*_~()[]{}“”‘’"""):
    return "".join(ch for ch in s if ch not in punctuation)


def round_to_n(x, n=5):
    if x == 0:
        return 0

    return round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))


with open("stop-words.txt") as f:
    stop_words = set(f.readlines())
    stop_words = set([word.strip() for word in stop_words])

with open("subcategories.txt") as f:
    SUBCATEGORIES = [line.strip() for line in f.readlines()]

word_to_subcat = {}
subcat_frequencies = [0 for subcat in SUBCATEGORIES]

for line in tqdm(questions[int(0.2 * len(questions)) :]):
    data = json.loads(line)

    if "subcategory" not in data:
        continue

    subcategory = data["subcategory"]

    if subcategory not in SUBCATEGORIES:
        continue

    subcategory_index = SUBCATEGORIES.index(subcategory)

    if data["type"] == "tossup" and "question" in data and "answer" in data:
        tokens = (
            removePunctuation(data["question"] + " " + data["answer"]).lower().split()
        )
    if (
        data["type"] == "bonus"
        and "leadin" in data
        and "parts" in data
        and "answers" in data
    ):
        tokens = (
            removePunctuation(
                data["leadin"]
                + " "
                + " ".join(data["parts"])
                + " "
                + " ".join(data["answers"])
            )
            .lower()
            .split()
        )

    tokens = [token for token in tokens if token not in stop_words]
    for token in tokens:
        if token not in word_to_subcat:
            word_to_subcat[token] = [0 for _ in range(len(SUBCATEGORIES))]

        word_to_subcat[token][subcategory_index] += 1

    subcat_frequencies[subcategory_index] += 1

with open("word-to-subcat.json", "w") as f:
    for word in word_to_subcat:
        word_to_subcat[word] = [
            i / frequency
            for i, frequency in zip(word_to_subcat[word], subcat_frequencies)
        ]
        word_to_subcat[word] = [round_to_n(i, 5) for i in word_to_subcat[word]]
    json.dump(word_to_subcat, f)

# with open('priors.json', 'w') as f:
#     priors = [frequency / sum(subcat_frequencies) for frequency in subcat_frequencies]
#     priors = [round_to_n(i, 5) for i in priors]
#     json.dump(priors, f)

# for word in word_to_subcat:
#     hhi_value = normalized_hhi(word_to_subcat[word])
#     factor = hhi_value**4 / sum(word_to_subcat[word])
#     word_to_subcat[word] = [factor * i for i in word_to_subcat[word]]
#     word_to_subcat[word] = [round_to_n(i, 5) for i in word_to_subcat[word]]

# with open('word-to-subcat-normalized.json', 'w') as f:
#     json.dump(word_to_subcat, f)
