import json
import math
import numpy as np
import os

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(CURRENT_PATH, "stop-words.txt")) as f:
    STOP_WORDS = set(f.readlines())
    STOP_WORDS = set([word.strip() for word in STOP_WORDS])

with open(os.path.join(CURRENT_PATH, "subcategories.txt")) as f:
    SUBCATEGORIES = [line.strip() for line in f.readlines()]

with open(os.path.join(CURRENT_PATH, "word-to-subcat.json")) as f:
    WORD_TO_SUBCAT_INFO = json.load(f)
    WORD_TO_SUBCAT_FREQUENCIES = WORD_TO_SUBCAT_INFO["frequencies"]
    SUBCATEGORY_FREQUENCIES = WORD_TO_SUBCAT_INFO["subcategory_frequencies"]
    PRIORS = [math.log(x) for x in SUBCATEGORY_FREQUENCIES]

with open(os.path.join(CURRENT_PATH, "../modules/subcat-to-cat.json")) as f:
    SUBCAT_TO_CAT = json.load(f)


def classify_question(question, type="tossup"):
    if type == "tossup":
        prediction = classify_subcategory(
            question["question"] + " " + question["answer"]
        )
    elif type == "bonus":
        prediction = classify_subcategory(
            question["leadin"]
            + " "
            + " ".join(question["parts"])
            + " ".join(question["answers"])
        )
    else:
        raise ValueError("type must be tossup or bonus")

    return SUBCAT_TO_CAT[prediction], prediction


def classify_subcategory(text, EPSILON=0.01):
    likelihoods = [i for i in PRIORS]
    SMOOTHED_SUBCATEGORY_FREQUENCIES = [
        math.log(x + EPSILON * len(SUBCATEGORIES)) for x in SUBCATEGORY_FREQUENCIES
    ]

    text = removePunctuation(text).lower().split()
    for token in text:
        if token in STOP_WORDS:
            continue

        if token not in WORD_TO_SUBCAT_FREQUENCIES:
            continue

        for i in range(len(SUBCATEGORIES)):
            likelihoods[i] += math.log(WORD_TO_SUBCAT_FREQUENCIES[token][i] + EPSILON)
            likelihoods[i] -= SMOOTHED_SUBCATEGORY_FREQUENCIES[i]

    max_likelihood = max(likelihoods)
    # as far as I can tell, there's always only one valid index
    valid_indices = [
        i for i, likelihood in enumerate(likelihoods) if likelihood == max_likelihood
    ]
    return SUBCATEGORIES[np.random.choice(valid_indices)]


def removePunctuation(s, punctuation=""".,!-;:'"\/?@#$%^&*_~()[]{}“”‘’"""):
    return "".join(ch for ch in s if ch not in punctuation)


if __name__ == "__main__":
    for line in open("input.txt"):
        data = json.loads(line.strip())
        prediction = classify_subcategory(data["text"])
        cat, subcat = SUBCAT_TO_CAT[prediction], prediction
        data["category"] = cat
        data["subcategory"] = subcat
        print(json.dumps(data, indent=None))
