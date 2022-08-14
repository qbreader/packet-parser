import json
import time


def classify(text):
    subcat = classify_subcategory(text)
    return (SUBCAT_TO_CAT[subcat], subcat)


def classify_subcategory(text):
    likelihoods = [0 for _ in range(len(SUBCATEGORIES))]
    text = set(removePunctuation(text).lower().split())
    for token in text:
        if token in STOP_WORDS:
            continue

        if token in word_to_subcat:
            for i in range(len(SUBCATEGORIES)):
                likelihoods[i] += word_to_subcat[token][i]
        else:
            print('Token not in word_to_subcat:', token)

    subcategory_index = likelihoods.index(max(likelihoods))
    return SUBCATEGORIES[subcategory_index]


def hhi(arr):
    return sum([_**2 for _ in arr]) / sum(arr) ** 2


def normalized_hhi(arr):
    return (hhi(arr) - 1/len(arr)) / (1 - 1/len(arr))


def removePunctuation(s, punctuation='''.,!-;:'"\/?@#$%^&*_~()[]{}“”‘’'''):
    return ''.join(ch for ch in s if ch not in punctuation)


with open('../stop-words.txt') as f:
    STOP_WORDS = set(f.readlines())
    STOP_WORDS = set([word.strip() for word in STOP_WORDS])

with open('../subcategories.txt') as f:
    SUBCATEGORIES = [line.strip() for line in f.readlines()]

with open('../subcat-to-cat.json') as f:
    SUBCAT_TO_CAT = json.load(f)

time_now = time.perf_counter()
with open('word-to-subcat-normalized.json') as f:
    word_to_subcat = json.load(f)
print('Time to load word_to_subcat:', time.perf_counter() - time_now)

# for word in word_to_subcat:
#     # factor = normalized_hhi(word_to_subcat[word])
#     factor = normalized_hhi(
#         word_to_subcat[word])**5 / sum(word_to_subcat[word])
#     word_to_subcat[word] = [factor * i for i in word_to_subcat[word]]


print('=====Begin Testing=====')
time_now = time.perf_counter()

questions = open('questions.json')
counter = 0
correct = 0
confusion_matrix = [[0 for _ in range(len(SUBCATEGORIES))]
                    for _ in range(len(SUBCATEGORIES))]
for line in questions:
    data = json.loads(line)
    if 'subcategory' not in data:
        continue

    counter += 1
    subcategory = data['subcategory']
    if subcategory not in SUBCATEGORIES:
        continue

    if data['type'] == 'tossup':
        prediction = classify_subcategory(data['question'])
    if data['type'] == 'bonus' and 'parts' in data and len(data['parts']) == 3:
        prediction = classify_subcategory(
            data['leadin'] + ' ' + data['parts'][0] + data['parts'][1] + data['parts'][2])

    # subcategory_index = SUBCATEGORIES.index(subcategory)
    # prediction_index = SUBCATEGORIES.index(prediction)

    # confusion_matrix[subcategory_index][prediction_index] += 1

    if subcategory in prediction:
        correct += 1

    if counter % 10000 == 0:
        print(f'{correct}/{counter}')

print('=====End Testing=====')
print(f'Accuracy: {correct / counter} ({correct}/{counter})')
print('Time:', time.perf_counter() - time_now, 'seconds')
# print('Confusion Matrix:')
# for row in confusion_matrix:
#     print(row)
