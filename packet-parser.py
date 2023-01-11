import json
import math
import os
import regex
import sys

import numpy as np


class bcolors:
    HEADER = '\x1b[95m'
    OKBLUE = '\x1b[94m'
    OKCYAN = '\x1b[96m'
    OKGREEN = '\x1b[92m'
    WARNING = '\x1b[93m'
    FAIL = '\x1b[91m'
    ENDC = '\x1b[0m'
    BOLD = '\x1b[1m'
    UNDERLINE = '\x1b[4m'


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


def classify_subcategory(text):
    likelihoods = [0 for _ in range(len(SUBCATEGORIES))]
    text = set(remove_punctuation(text).lower().split())
    for token in text:
        if token in STOP_WORDS:
            continue

        if token in WORD_TO_SUBCAT:
            for i in range(len(SUBCATEGORIES)):
                likelihoods[i] += math.log(WORD_TO_SUBCAT[token][i] + 0.00000001)
        else:
            # print('Token not in word-to-subcat:', token)
            pass

    max_likelihood = max(likelihoods)
    # as far as I can tell, there's always only one valid index
    valid_indices = [i for i, likelihood in enumerate(likelihoods) if likelihood == max_likelihood]
    return SUBCATEGORIES[np.random.choice(valid_indices)]


def format_text(text):
    return text \
        .replace('{bu}', '<b><u>') \
        .replace('{/bu}', '</u></b>') \
        .replace('{u}', '<u>') \
        .replace('{/u}', '</u>') \
        .replace('{i}', '<i>') \
        .replace('{/i}', '</i>')


def get_subcategory(text: str):
    text = text.lower()
    for subcat in STANDARDIZE_SUBCATS:
        works = True
        for word in regex.split(f'[\/ ]', subcat.lower()):
            if word not in text:
                works = False
                break
        if works:
            return STANDARDIZE_SUBCATS[subcat]

    return ''


def remove_formatting(text: str, include_italics=False):
    text = text.replace('{bu}', '').replace('{/bu}', '').replace('{u}', '').replace('{/u}', '')

    if not include_italics:
        text = text.replace('{i}', '').replace('{/i}', '')

    return text


def remove_punctuation(s: str, punctuation='''.,!-;:'"\/?@#$%^&*_~()[]{}“”‘’'''):
    return ''.join(ch for ch in s if ch not in punctuation)


INPUT_DIRECTORY = 'packets/'
OUTPUT_DIRECTORY = 'output/'

FORMATTED_ANSWERLINE = (len(sys.argv) == 2 and sys.argv[1] == '-f')

HAS_CATEGORY_TAGS = (input('Do you have category tags? (y/n) ') == 'y')
print('Using category tags' if HAS_CATEGORY_TAGS else 'Using question classifier')

HAS_QUESTION_NUMBERS = (input('Do you have question numbers? (y/n) ') == 'y')

try:
    os.mkdir(OUTPUT_DIRECTORY)
except FileExistsError:
    print(f'{bcolors.WARNING}WARNING:{bcolors.ENDC} Output directory already exists')
    if not input('Continue? (y/n) ') == 'y':
        exit(0)

REGEX_FLAGS = regex.IGNORECASE | regex.MULTILINE

if HAS_CATEGORY_TAGS and HAS_QUESTION_NUMBERS:
    REGEX_QUESTION = r'^ *\d{1,2}\.(?:.|\n)*?ANSWER(?:.|\n)*?<[^>]*>'
    # old regex for has question numbers and no category tags
    # REGEX_QUESTION = r'^ *\d{1,2}\.(?:.|\n)*?ANSWER(?:.*\n)*?(?= *\d{1,2}\.)'
elif HAS_QUESTION_NUMBERS:
    REGEX_QUESTION = r'\d{1,2}(?:[^\d\n].*\n)*[ \t]*ANSWER.*(?:\n.+)*?(?=\n\d{1,2}|\n$)'
else:
    REGEX_QUESTION = r'(?:[^\n].*\n)*[ \t]*ANSWER.*(?:\n.*)*?(?=\n$)'

REGEX_CATEGORY_TAG = r'<[^>]*>'

REGEX_TOSSUP_TEXT = r'(?<=\d{1,2}\.)(?:.|\n)*?(?=^ ?ANSWER|ANSWER:)'
REGEX_TOSSUP_ANSWER = r'(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*(?=<[^>]*>)' if HAS_CATEGORY_TAGS else r'(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*'

REGEX_BONUS_LEADIN = r'(?<=^ *\d{1,2}\.)(?:.|\n)*?(?=\[(?:10)?[EMH]?\])'
REGEX_BONUS_PARTS = r'(?<=\[(?:10)?[EMH]?\])(?:.|\n)*?(?= ?ANSWER|ANSWER:)'
REGEX_BONUS_ANSWERS = r'(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*?(?=\[(?:10)?[EMH]?\]|<[^>]*>)'

EXPECTED_BONUS_LENGTH = 3

with open('standardize-subcats.json') as f:
    STANDARDIZE_SUBCATS = json.load(f)


with open('stop-words.txt') as f:
    STOP_WORDS = set(f.readlines())
    STOP_WORDS = set([word.strip() for word in STOP_WORDS])


with open('subcat-to-cat.json') as f:
    SUBCAT_TO_CAT = json.load(f)


with open('subcategories.txt') as f:
    SUBCATEGORIES = [line.strip() for line in f.readlines()]


with open('classifier/word-to-subcat-normalized.json') as f:
    WORD_TO_SUBCAT = json.load(f)


for filename in sorted(os.listdir(INPUT_DIRECTORY)):
    if filename == '.DS_Store':
        continue

    f = open(INPUT_DIRECTORY + filename)
    packet_text = ''
    for line in f.readlines():
        packet_text += line

    packet_text = packet_text + '\n0.'
    packet_text = packet_text.replace('', '')
    # remove zero-width U+200b character that appears in the text
    packet_text = packet_text \
        .replace('​', '') \
        .replace('{/bu}{bu}', '') \
        .replace('{/u}{u}', '') \
        .replace('{/i}{i}', '') \
        .replace('{i}\n{/i}', '\n') \
        .replace('{i} {/i}', ' ') \
        .replace('ANWER:', 'ANSWER:') \
        .replace('ANSER:', 'ANSWER:') \
        .replace('ANSWR:', 'ANSWER:') \
        .replace('ASNWER:', 'ANSWER:') \
        .replace('ANSEWR:', 'ANSWER:') \
        .replace('Anwer:', 'Answer:') \
        .replace('Anser:', 'Answer:') \
        .replace('Answr:', 'Answer:') \
        .replace('Asnwer:', 'Answer:') \
        .replace('Ansewr:', 'ANSWER:') \
        .replace('FTPE', 'For 10 points each') \
        .replace('FTP', 'For 10 points') \
        .replace('[5,5]', '[10]') \
        .replace('[5/5]', '[10]') \
        .replace('[5, 5]', '[10]') \
        .replace('\n[5]', '\n[10]') \
        .replace('\n(10)', '\n[10]') \
        .replace('[10[', '[10]') \
        .replace(']10]', '[10]') \

    packet_text = regex.sub(r'\(\d{1,2}|TB\)', '1.', packet_text)
    packet_text = regex.sub(r'^(\d{1,2}|TB)\)', '1.', packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r'^TB[\.:]?', '21.', packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r'^Tiebreaker[\.:]?', '21.', packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r'^Extra[\.:]?', '21.', packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r'ten\spoints', '10 points', packet_text)

    packet_questions = regex.findall(REGEX_QUESTION, packet_text, flags=REGEX_FLAGS)

    tossups = []
    bonuses = []

    for question in packet_questions:
        if not HAS_QUESTION_NUMBERS or regex.match('^\d{1,2}\. ', question) == None:
            question = '1. ' + question

        if regex.findall(r'^\[(?:10)?[EMH]?\]', question, flags=REGEX_FLAGS):
            bonuses.append(question)
        else:
            tossups.append(question)

    print(f'Found {len(tossups):2} tossups and {len(bonuses):2} bonuses in file {bcolors.OKBLUE}{filename}{bcolors.ENDC}')

    data = {
        'tossups': [],
        'bonuses': []
    }

    skipped_tossups = 0
    for i, tossup in enumerate(tossups):
        try:
            question = regex.findall(REGEX_TOSSUP_TEXT, remove_formatting(tossup), flags=REGEX_FLAGS)
            question = question[0].strip().replace('\n', ' ')
        except:
            print(f'{bcolors.FAIL}ERROR:{bcolors.ENDC} {i+1} cannot find question text for tossup - ', tossup)
            exit(1)

        data['tossups'].append({'question': question})
        if 'answer:' in question.lower() or len(regex.findall(r'\(\*\)', question)) == 2:
            print(f'{bcolors.WARNING}WARNING:{bcolors.ENDC} tossup {i + 1 + skipped_tossups} question may contain the next question')
            skipped_tossups += 1

        answer = regex.findall(REGEX_TOSSUP_ANSWER, tossup, flags=REGEX_FLAGS)

        try:
            answer = answer[0].strip().replace('\n', ' ')
            if answer.startswith(':'):
                answer = answer[1:].strip()
        except:
            print(f'{bcolors.FAIL}ERROR:{bcolors.ENDC} {i+1} cannot find answer for tossup - ', tossup)
            exit(1)

        if FORMATTED_ANSWERLINE:
            data['tossups'][i]['formatted_answer'] = format_text(answer)
            answer = remove_formatting(answer)

        data['tossups'][i]['answer'] = answer
        if 'answer:' in answer.lower():
            print(f'{bcolors.WARNING}WARNING:{bcolors.ENDC} tossup {i + 1 + skipped_tossups} answer may contain the next question')
            skipped_tossups += 1

        if HAS_CATEGORY_TAGS:
            category_tag = regex.findall(
                REGEX_CATEGORY_TAG,
                remove_formatting(tossup),
                flags=REGEX_FLAGS
            )[0].strip().replace('\n', ' ')
            cat = get_subcategory(category_tag)
            if len(cat) == 0:
                print(f'{bcolors.WARNING}WARNING:{bcolors.ENDC} tossup {i + 1} has unrecognized subcategory', category_tag)
            else:
                data['tossups'][i]['subcategory'] = cat
                data['tossups'][i]['category'] = SUBCAT_TO_CAT[cat]
        else:
            category, subcategory = classify_question(data['tossups'][i], type='tossup')
            data['tossups'][i]['category'] = category
            data['tossups'][i]['subcategory'] = subcategory

    skipped_bonuses = 0
    for i, bonus in enumerate(bonuses):
        try:
            leadin = regex.findall(REGEX_BONUS_LEADIN, remove_formatting(bonus), flags=REGEX_FLAGS)
            leadin = leadin[0].strip().replace('\n', ' ')
        except:
            print(f'{bcolors.FAIL}ERROR:{bcolors.ENDC} cannot find leadin for bonus {i + 1} - ', bonus)
            exit(2)

        data['bonuses'].append({'leadin': leadin})

        if 'answer:' in leadin.lower():
            print(f'{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1 + skipped_bonuses} leadin may contain the previous question')
            skipped_bonuses += 1

        data['bonuses'][i]['parts'] = []
        parts = regex.findall(REGEX_BONUS_PARTS, remove_formatting(bonus), flags=REGEX_FLAGS)

        if len(parts) > EXPECTED_BONUS_LENGTH:
            print(f'{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1} has more than {EXPECTED_BONUS_LENGTH} parts')

        for part in parts:
            part = part.strip().replace('\n', ' ')
            data['bonuses'][i]['parts'].append(part)

        data['bonuses'][i]['values'] = [10 for _ in range(len(data['bonuses'][i]['parts']))]
        data['bonuses'][i]['answers'] = []

        bonus = bonus + '\n[10]'

        if FORMATTED_ANSWERLINE:
            data['bonuses'][i]['formatted_answers'] = []

        answers = regex.findall(REGEX_BONUS_ANSWERS, bonus, flags=REGEX_FLAGS)
        for answer in answers:
            answer = answer.strip().replace('\n', ' ')

            if answer.startswith(':'):
                answer = answer[1:].strip()

            if FORMATTED_ANSWERLINE:
                data['bonuses'][i]['formatted_answers'].append(format_text(answer))
                answer = remove_formatting(answer)

            data['bonuses'][i]['answers'].append(answer)

        bonus = bonus[:-5]

        if HAS_CATEGORY_TAGS:
            category_tag = regex.findall(REGEX_CATEGORY_TAG, remove_formatting(bonus), flags=REGEX_FLAGS)[0]
            category_tag = category_tag.strip().replace('\n', ' ')
            cat = get_subcategory(category_tag)

            if len(cat) == 0:
                print(f'{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1} has unrecognized subcategory', category_tag)
            else:
                data['bonuses'][i]['subcategory'] = cat
                data['bonuses'][i]['category'] = SUBCAT_TO_CAT[cat]
        else:
            if 'parts' not in data['bonuses'][i]:
                print(f'{bcolors.FAIL}ERROR:{bcolors.ENDC} no parts found for bonus {i+1} - ', bonus)
                exit(2)

            if len(data['bonuses'][i]['parts']) < EXPECTED_BONUS_LENGTH:
                print(f'{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1} has fewer than {EXPECTED_BONUS_LENGTH} parts')
                if not HAS_QUESTION_NUMBERS:
                    print()
                    print(bonus[3:])
                    print()

                continue

            category, subcategory = classify_question(data['bonuses'][i], type='bonus')
            data['bonuses'][i]['category'] = category
            data['bonuses'][i]['subcategory'] = subcategory

    g = open(OUTPUT_DIRECTORY + filename[:-4] + '.json', 'w')
    json.dump(data, g)
