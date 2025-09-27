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

with open(os.path.join(CURRENT_PATH, "subcategory-to-category.json")) as f:
    SUBCATEGORY_TO_CATEGORY = json.load(f)

with open(os.path.join(CURRENT_PATH, "alternate-subcategories.json")) as f:
    ALTERNATE_SUBCATEGORIES = json.load(f)

with open(os.path.join(CURRENT_PATH, "subsubcategories.json")) as f:
    SUBSUBCATEGORIES = json.load(f)

with open(os.path.join(CURRENT_PATH, "classifier-subcategory.json")) as f:
    data = json.load(f)
    WORD_TO_SUBCATEGORY = data["word_to_subcategory"]
    SUBCATEGORY_FREQUENCIES = data["subcategory_frequencies"]

with open(os.path.join(CURRENT_PATH, "classifier-alternate-subcategory.json")) as f:
    data = json.load(f)
    WORD_TO_ALTERNATE_SUBCATEGORY = data["word_to_alternate_subcategory"]
    ALTERNATE_SUBCATEGORY_FREQUENCIES = data["alternate_subcategory_frequencies"]

with open(os.path.join(CURRENT_PATH, "classifier-subsubcategory.json")) as f:
    data = json.load(f)
    WORD_TO_SUBSUBCATEGORY = data["word_to_subsubcategory"]
    SUBSUBCATEGORY_FREQUENCIES = data["subsubcategory_frequencies"]

with open(os.path.join(CURRENT_PATH, "../modules/subcat-to-cat.json")) as f:
    SUBCAT_TO_CAT = json.load(f)


def classify_question(text, fixed_category=None) -> tuple[str, str, str]:
    subcategory = classify(text, mode="subcategory", category=fixed_category)
    category = SUBCAT_TO_CAT[subcategory]
    alternate_subcategory = ""

    if category in ALTERNATE_SUBCATEGORIES:
        alternate_subcategory = classify(
            text, mode="alternate-subcategory", category=category
        )

    if subcategory in SUBSUBCATEGORIES:
        # TODO: change to subsubcategory
        alternate_subcategory = classify(
            text, mode="subsubcategory", subcategory=subcategory
        )

    return SUBCAT_TO_CAT[subcategory], subcategory, alternate_subcategory


def classify(text, mode="subcategory", category="", subcategory="", EPSILON=0.01):
    if mode == "subcategory":
        if category:
            valid_indices = []
            for i, subcategory in enumerate(SUBCATEGORIES):
                if SUBCATEGORY_TO_CATEGORY[subcategory] == category:
                    valid_indices.append(i)
        else:
            valid_indices = None
        index = naive_bayes_classify(
            text,
            WORD_TO_SUBCATEGORY,
            SUBCATEGORY_FREQUENCIES,
            valid_indices=valid_indices,
            EPSILON=EPSILON,
        )
        return SUBCATEGORIES[index]

    if mode == "alternate-subcategory":
        if category not in ALTERNATE_SUBCATEGORIES:
            message = f"Category {category} does not have alternate subcategories."
            raise ValueError(message)

        index = naive_bayes_classify(
            text,
            WORD_TO_ALTERNATE_SUBCATEGORY[category],
            ALTERNATE_SUBCATEGORY_FREQUENCIES[category],
            EPSILON=EPSILON,
        )
        return ALTERNATE_SUBCATEGORIES[category][index]

    if mode == "subsubcategory":
        if subcategory not in SUBSUBCATEGORIES:
            message = f"Subcategory {subcategory} does not have subsubcategories."
            raise ValueError(message)

        index = naive_bayes_classify(
            text,
            WORD_TO_SUBSUBCATEGORY[subcategory],
            SUBSUBCATEGORY_FREQUENCIES[subcategory],
            EPSILON=EPSILON,
        )
        return SUBSUBCATEGORIES[subcategory][index]


def naive_bayes_classify(
    text,
    WORD_TO_FREQUENCY,
    CLASS_FREQUENCIES,
    valid_indices=None,
    EPSILON=0.01,
):
    """
    Returns the index of the class prediction.
    """
    likelihoods = [math.log(x) for x in CLASS_FREQUENCIES]
    SMOOTHED_CLASS_FREQUENCIES = [
        math.log(x + EPSILON * len(CLASS_FREQUENCIES)) for x in CLASS_FREQUENCIES
    ]

    text = removePunctuation(text).lower().split()
    for token in text:
        if token in STOP_WORDS:
            continue

        if token not in WORD_TO_FREQUENCY:
            continue

        for i in range(len(CLASS_FREQUENCIES)):
            likelihoods[i] += math.log(WORD_TO_FREQUENCY[token][i] + EPSILON)
            likelihoods[i] -= SMOOTHED_CLASS_FREQUENCIES[i]

    if valid_indices is not None:
        for i in range(len(likelihoods)):
            if i not in valid_indices:
                likelihoods[i] = -math.inf

    max_likelihood = max(likelihoods)
    # as far as I can tell, there's always only one valid index
    valid_indices = [
        i for i, likelihood in enumerate(likelihoods) if likelihood == max_likelihood
    ]
    return np.random.choice(valid_indices)


def removePunctuation(s, punctuation=""".,!-;:'"\\/?@#$%^&*_~()[]{}“”‘’"""):
    return "".join(ch for ch in s if ch not in punctuation)


if __name__ == "__main__":
    for line in open("input.txt"):
        data = json.loads(line.strip())
        category, subcategory, alternate_subcategory = classify(
            data["text"], data["type"]
        )
        data["category"] = category
        data["subcategory"] = subcategory
        print(json.dumps(data, indent=None))
