import json
import os
import regex
import sys


def classify_question(question, type='tossup'):
    if type == 'tossup':
        prediction = classify_subcategory(question['question'])
    elif type == 'bonus':
        prediction = classify_subcategory(
            question['leadin'] + ' ' + question['parts'][0] + ' ' + question['parts'][1] + ' ' + question['parts'][2])
    else:
        raise ValueError('type must be tossup or bonus')

    return SUBCAT_TO_CAT[prediction], prediction


def classify_subcategory(text):
    likelihoods = [0 for _ in range(len(SUBCATEGORIES))]
    text = set(remove_punctuation(text).lower().split())
    for token in text:
        if token in STOP_WORDS:
            continue

        if token in WORD_TO_SUBCAT:
            for i in range(len(SUBCATEGORIES)):
                likelihoods[i] += WORD_TO_SUBCAT[token][i]
        else:
            pass
            # print('Token not in word_to_subcat:', token)

    subcategory_index = likelihoods.index(max(likelihoods))
    return SUBCATEGORIES[subcategory_index]


def remove_formatting(text):
    return text.replace('{bu}', '').replace('{/bu}', '').replace('{u}', '').replace('{/u}', '')


def remove_punctuation(s, punctuation='''.,!-;:'"\/?@#$%^&*_~()[]{}“”‘’'''):
    return ''.join(ch for ch in s if ch not in punctuation)


def get_subcategory(s):
    s = s.lower()
    for key in STANDARDIZE_SUBCATS:
        works = True
        for word in regex.split(f'[\/ ]', key.lower()):
            if word not in s:
                works = False
                break
        if works:
            return STANDARDIZE_SUBCATS[key]

    return ''


HAS_CATEGORY_TAGS = (input("Do you have category tags? (y/n) ") == "y")
FORMATTED_ANSWERLINE = (len(sys.argv) == 2 and sys.argv[1] == '-f')
print('Using category tags' if HAS_CATEGORY_TAGS else 'Using question classifier')
INPUT_DIRECTORY = 'packets/'
OUTPUT_DIRECTORY = 'output/'
try:
    os.mkdir(OUTPUT_DIRECTORY)
except FileExistsError:
    print('Output directory already exists')

REGEX_FLAGS = regex.IGNORECASE | regex.MULTILINE

REGEX_QUESTION = r'^\d{1,2}\.(?:.|\n)*?ANSWER(?:.|\n)*?<[^>]*>' if HAS_CATEGORY_TAGS else r'^\d{1,2}\.(?:.|\n)*?ANSWER(?:.*\n)*?(?=\d{1,2}\.)'
REGEX_CATEGORY_TAG = r'<[^>]*>'

REGEX_TOSSUP_TEXT = r'(?<=\d{1,2}\.)(?:.|\n)*?(?=^ ?ANSWER|ANSWER:)'
REGEX_TOSSUP_ANSWER = r'(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*(?=<[^>]*>)' if HAS_CATEGORY_TAGS else r'(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*'

REGEX_BONUS_LEADIN = r'(?<=^\d{1,2}\.)(?:.|\n)*?(?=\n\[)'
REGEX_BONUS_PARTS = r'(?<=\[(?:10)?[EMH]?\])(?:.|\n)*?(?= ?ANSWER|ANSWER:)'
REGEX_BONUS_ANSWERS = r'(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*?(?=\[(?:10)?[EMH]?\]|<[^>]*>)'


with open('standardize-subcats.json') as f:
    STANDARDIZE_SUBCATS = json.load(f)


with open('stop-words.txt') as f:
    STOP_WORDS = set(f.readlines())
    STOP_WORDS = set([word.strip() for word in STOP_WORDS])


with open('subcat-to-cat.json') as f:
    SUBCAT_TO_CAT = json.load(f)


with open('subcategories.txt') as f:
    SUBCATEGORIES = [line.strip() for line in f.readlines()]


with open('classifier/word_to_subcat_normalized.json') as f:
    WORD_TO_SUBCAT = json.load(f)


for file in os.listdir(INPUT_DIRECTORY):
    if file == '.DS_Store':
        continue

    f = open(INPUT_DIRECTORY + file)
    g = open(OUTPUT_DIRECTORY + file[:-4] + '.json', 'w')

    data = {
        'tossups': [],
        'bonuses': []
    }

    packet_text = ''
    for line in f.readlines():
        packet_text += line

    packet_text = packet_text + '\n0.'
    packet_text = packet_text.replace('', '')
    # remove zero-width U+200b character that appears in the text
    packet_text = packet_text.replace('​', '')
    packet_text = packet_text.replace('ANWER:', 'ANSWER:')
    packet_text = packet_text.replace('ANSER:', 'ANSWER:')
    packet_text = packet_text.replace('ANSWR:', 'ANSWER:')
    packet_text = packet_text.replace('Anwer:', 'Answer:')
    packet_text = packet_text.replace('Anser:', 'Answer:')
    packet_text = packet_text.replace('Answr:', 'Answer:')
    packet_text = packet_text.replace('FTPE', 'For 10 points each')
    packet_text = packet_text.replace('FTP', 'For 10 points')
    packet_text = regex.sub(r'^TB[\.:]?', '21.',
                            packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r'^Tiebreaker\.?', '21.',
                            packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r'ten\spoints', '10 points', packet_text)
    packet_text = regex.sub(r'\(\d{1,2}\)', '1.', packet_text)
    packet_questions = regex.findall(
        REGEX_QUESTION, packet_text, flags=REGEX_FLAGS)

    tossups = []
    bonuses = []

    for q in packet_questions:
        if regex.findall(r'\[(?:10)?[EMH]?\]', q, flags=regex.IGNORECASE):
            bonuses.append(q)
        else:
            tossups.append(q)

    print(f'{file}: parsed {len(tossups)} tossups and {len(bonuses)} bonuses')

    for i, tossup in enumerate(tossups):
        try:
            question = regex.findall(REGEX_TOSSUP_TEXT, remove_formatting(
                tossup), flags=REGEX_FLAGS)[0].strip().replace('\n', ' ')
        except:
            print("TOSSUP ERROR:", tossup)
            exit(1)
        data['tossups'].append({'question': question})

        answer = regex.findall(REGEX_TOSSUP_ANSWER, tossup, flags=REGEX_FLAGS)[
            0].strip().replace('\n', ' ')
        if answer.startswith(':'):
            answer = answer[1:].strip()

        if FORMATTED_ANSWERLINE:
            data['tossups'][i]['answer_formatted'] = answer.replace('{bu}', '<b><u>').replace(
                '{/bu}', '</u></b>').replace('{u}', '<u>').replace('{/u}', '</u>')
            answer = remove_formatting(answer)

        data['tossups'][i]['answer'] = answer

        if HAS_CATEGORY_TAGS:
            j = regex.findall(REGEX_CATEGORY_TAG, remove_formatting(
                tossup), flags=REGEX_FLAGS)[0].strip().replace('\n', ' ')
            cat = get_subcategory(j)
            if len(cat) == 0:
                print(i+1, 'tossup - ERROR: unrecognized subcategory', j)
            else:
                data['tossups'][i]['subcategory'] = cat
                data['tossups'][i]['category'] = SUBCAT_TO_CAT[cat]

    for i, bonus in enumerate(bonuses):
        try:
            leadin = regex.findall(REGEX_BONUS_LEADIN, remove_formatting(
                bonus), flags=REGEX_FLAGS)[0].strip().replace('\n', ' ')
        except:
            print("BONUS ERROR:", bonus)
            exit(1)
        data['bonuses'].append({'leadin': leadin})

        data['bonuses'][i]['parts'] = []
        parts = regex.findall(REGEX_BONUS_PARTS, remove_formatting(
            bonus), flags=REGEX_FLAGS)
        for part in parts:
            part = part.strip().replace('\n', ' ')
            part = part
            data['bonuses'][i]['parts'].append(part)

        bonus = bonus + '\n[10]'
        data['bonuses'][i]['answers'] = []
        if FORMATTED_ANSWERLINE:
            data['bonuses'][i]['answers_formatted'] = []

        answers = regex.findall(
            REGEX_BONUS_ANSWERS, bonus, flags=REGEX_FLAGS)
        for answer in answers:
            answer = answer.strip().replace('\n', ' ')
            if answer.startswith(':'):
                answer = answer[1:].strip()
            if FORMATTED_ANSWERLINE:
                data['bonuses'][i]['answers_formatted'].append(answer.replace('{bu}', '<b><u>').replace(
                    '{/bu}', '</u></b>').replace('{u}', '<u>').replace('{/u}', '</u>'))
                answer = answer.replace('{bu}', '').replace(
                    '{/bu}', '').replace('{u}', '').replace('{/u}', '')
            data['bonuses'][i]['answers'].append(answer)
        bonus = bonus[:-5]

        if HAS_CATEGORY_TAGS:
            j = regex.findall(REGEX_CATEGORY_TAG, remove_formatting(
                bonus), flags=REGEX_FLAGS)[0].strip().replace('\n', ' ')
            cat = get_subcategory(j)
            if len(cat) == 0:
                print(i+1, 'bonus - ERROR: unrecognized subcategory', j)
            else:
                data['bonuses'][i]['subcategory'] = cat
                data['bonuses'][i]['category'] = SUBCAT_TO_CAT[cat]

    if not HAS_CATEGORY_TAGS:
        for tossup in data['tossups']:
            category, subcategory = classify_question(tossup, type='tossup')
            tossup['category'] = category
            tossup['subcategory'] = subcategory

        for i, bonus in enumerate(data['bonuses']):
            if 'parts' not in bonus:
                print(i+1, 'bonus - ERROR: no parts found for bonus')
                continue
            if len(bonus['parts']) < 3:
                print(i+1, 'bonus - ERROR: has fewer than 3 parts')
                continue
            category, subcategory = classify_question(bonus, type='bonus')
            bonus['category'] = category
            bonus['subcategory'] = subcategory

    json.dump(data, g)
