"""
Note: needs the questions.json file in the same directory as this file.
It should contain all of the questions in the database dumped from mongodb.
"""

import json
import math
import numpy as np
from tqdm import tqdm

np.random.seed(0)

tossups = open("tossups.json").readlines()
bonuses = open("bonuses.json").readlines()
questions = tossups + bonuses
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

with open("alternate-subcategories.json") as f:
    ALTERNATE_SUBCATEGORIES = json.load(f)

with open("subsubcategories.json") as f:
    SUBSUBCATEGORIES = json.load(f)

word_to_subcategory = {}
word_to_alternate_subcategory = {category: {} for category in ALTERNATE_SUBCATEGORIES}
word_to_subsubcategory = {subcategory: {} for subcategory in SUBSUBCATEGORIES}
subcategory_frequencies = [0 for subcategory in SUBCATEGORIES]
alternate_subcategory_frequencies = {
    category: [0 for subcategory in ALTERNATE_SUBCATEGORIES[category]]
    for category in ALTERNATE_SUBCATEGORIES
}
subsubcategory_frequencies = {
    subcategory: [0 for subsubcategory in SUBSUBCATEGORIES[subcategory]]
    for subcategory in SUBSUBCATEGORIES
}

for line in tqdm(questions[int(0.2 * len(questions)) :]):
    data = json.loads(line)
    data["type"] = "tossup" if "question" in data else "bonus"

    if "category" not in data or "subcategory" not in data:
        continue

    category = data["category"]
    subcategory = data["subcategory"]

    if subcategory not in SUBCATEGORIES:
        continue

    subcategory_index = SUBCATEGORIES.index(subcategory)

    if (
        data["type"] == "tossup"
        and "question_sanitized" in data
        and "answer_sanitized" in data
    ):
        tokens = (
            removePunctuation(
                data["question_sanitized"] + " " + data["answer_sanitized"]
            )
            .lower()
            .split()
        )
    if (
        data["type"] == "bonus"
        and "leadin_sanitized" in data
        and "parts_sanitized" in data
        and "answers_sanitized" in data
    ):
        tokens = (
            removePunctuation(
                data["leadin_sanitized"]
                + " "
                + " ".join(data["parts_sanitized"])
                + " "
                + " ".join(data["answers_sanitized"])
            )
            .lower()
            .split()
        )

    tokens = [token for token in tokens if token not in stop_words]
    for token in tokens:
        if token not in word_to_subcategory:
            word_to_subcategory[token] = [0 for _ in range(len(SUBCATEGORIES))]

        word_to_subcategory[token][subcategory_index] += 1

    subcategory_frequencies[subcategory_index] += 1

    if (
        category in word_to_alternate_subcategory
        and "alternate_subcategory" in data
        and data["alternate_subcategory"] in ALTERNATE_SUBCATEGORIES[category]
    ):
        alternate_subcategory = data["alternate_subcategory"]
        index = ALTERNATE_SUBCATEGORIES[category].index(alternate_subcategory)

        for token in tokens:
            if token not in word_to_alternate_subcategory[category]:
                word_to_alternate_subcategory[category][token] = [
                    0 for _ in range(len(ALTERNATE_SUBCATEGORIES[category]))
                ]

            word_to_alternate_subcategory[category][token][index] += 1

        alternate_subcategory_frequencies[category][index] += 1

    if (
        subcategory in word_to_subsubcategory
        and "alternate_subcategory" in data
        and data["alternate_subcategory"] in SUBSUBCATEGORIES[subcategory]
    ):
        # TODO: change this to subsubcategory
        subsubcategory = data["alternate_subcategory"]
        index = SUBSUBCATEGORIES[subcategory].index(subsubcategory)

        for token in tokens:
            if token not in word_to_subsubcategory[subcategory]:
                word_to_subsubcategory[subcategory][token] = [
                    0 for _ in range(len(SUBSUBCATEGORIES[subcategory]))
                ]

            word_to_subsubcategory[subcategory][token][index] += 1

        subsubcategory_frequencies[subcategory][index] += 1

with open("classifier-subcategory.json", "w") as f:
    json.dump(
        {
            "word_to_subcategory": word_to_subcategory,
            "subcategory_frequencies": subcategory_frequencies,
        },
        f,
    )

with open("classifier-alternate-subcategory.json", "w") as f:
    json.dump(
        {
            "word_to_alternate_subcategory": word_to_alternate_subcategory,
            "alternate_subcategory_frequencies": alternate_subcategory_frequencies,
        },
        f,
    )

with open("classifier-subsubcategory.json", "w") as f:
    json.dump(
        {
            "word_to_subsubcategory": word_to_subsubcategory,
            "subsubcategory_frequencies": subsubcategory_frequencies,
        },
        f,
    )
