import json
import os
import regex
import sys
import time


HAS_CATEGORY_TAGS = (input("Do you have category tags? (y/n) ") == "y")
FORMATTED_ANSWERLINE = (len(sys.argv) == 2 and sys.argv[1] == '-f')
if HAS_CATEGORY_TAGS:
    print('Using category tags')
else:
    print('Using question classifier')

INPUT_DIRECTORY = 'packets/'
OUTPUT_DIRECTORY = 'output/'
try:
    os.mkdir(OUTPUT_DIRECTORY)
except FileExistsError:
    print('Output directory already exists')


REGEX_QUESTION = r'^\d{1,2}\.(?:.|\n)*?ANSWER(?:.|\n)*?<[^>]*>' if HAS_CATEGORY_TAGS else r'^\d{1,2}\.(?:.|\n)*?ANSWER(?:.*\n)*?(?=\d{1,2}\.)'
REGEX_CATEGORY_TAG = r'<[^>]*>'

REGEX_TOSSUP_TEXT = r'(?<=\d{1,2}\.)(?:.|\n)*?(?=^ ?ANSWER|ANSWER:)'
REGEX_TOSSUP_ANSWER = r'(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*(?=<[^>]*>)' if HAS_CATEGORY_TAGS else r'(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*'

REGEX_BONUS_LEADIN = r'(?<=^\d{1,2}\.)(?:.|\n)*?(?=\n\[)'
REGEX_BONUS_PARTS = r'(?<=\[(?:10)?[EMH]?\])(?:.|\n)*?(?= ?ANSWER|ANSWER:)'
REGEX_BONUS_ANSWERS = r'(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*?(?=\[(?:10)?[EMH]?\]|<[^>]*>)'

with open('standardize-subcats.json') as f:
    standarize_subcats = json.load(f)

with open('subcat-to-cat.json') as f:
    subcat_to_cat = json.load(f)

with open('stop_words.txt') as f:
    stop_words = set(f.readlines())
    stop_words = set([word.strip() for word in stop_words])


all_questions = []
for (dirpath, dirnames, filenames) in os.walk('packets_classify'):
    for filename in filenames:
        if filename == '.DS_Store': continue

        f = open(dirpath + '/' + filename)

        try:
            data = json.load(f)
        except:
            print(dirpath + '/' + filename)
            continue

        all_questions.append(data)


def remove_formatting(text):
    return text.replace('{bu}', '').replace('{/bu}', '').replace('{u}', '').replace('{/u}', '')


def removePunctuation(s, punctuation='''.,!-;:'"\/?@#$%^&*_~'''):
    return ''.join(ch for ch in s if ch not in punctuation)


def get_subcategory(s):
    s = s.lower()
    for key in standarize_subcats:
        works = True
        for word in regex.split(f'[\/ ]', key.lower()):
            if word not in s:
                works = False
                break
        if works:
            return standarize_subcats[key]

    return ''


def difference(text1, text2):
    '''
    Returns the number of words in common between the two strings
    '''
    count = 0

    words1 = text1
    words2 = text2
    for word in words1:
        # skip small common words
        # if len(word) < 5: continue
        if word in words2: count += len(word)

    return count


def classify_question(text, is_tossup, max_number_to_check=100000):
    i = 0
    text = set(text.split())
    text = set([removePunctuation(word).lower() for word in text])
    text = set([word for word in text if word not in stop_words])

    best_questions = []
    for data in all_questions:
        # 1 nearest neighbor LOL
        if is_tossup:
            if len(data['tossups']) > 0:
                best_questions.append(max(data['tossups'], key=lambda x: -100 if 'subcategory' not in x else difference(x['question'], text)))

            i += len(data['tossups'])
        elif 'bonuses' in data:
            if len(data['bonuses']) > 0:
                best_questions.append(max(data['bonuses'], key=lambda x: -100 if 'subcategory' not in x else difference(x['leadin'], text)))

            i += len(data['bonuses'])

        if i > max_number_to_check:
            break

    if is_tossup:
        best = max(best_questions, key=lambda x: -100 if 'subcategory' not in x else difference(x['question'], text))
    else:
        best = max(best_questions, key=lambda x: -100 if 'subcategory' not in x else difference(x['leadin'], text))

    return best['category'], best['subcategory']


for file in os.listdir(INPUT_DIRECTORY):
    if file == '.DS_Store': continue

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
    packet_text = packet_text.replace('​', '') # remove zero-width U+200b character that appears in the text
    packet_text = packet_text.replace('NSWER:', 'ANSWER:')
    packet_text = packet_text.replace('ANWER:', 'ANSWER:')
    packet_text = packet_text.replace('ANSER:', 'ANSWER:')
    packet_text = packet_text.replace('ANSWR:', 'ANSWER:')
    packet_text = packet_text.replace('nswer:', 'Answer:')
    packet_text = packet_text.replace('Anwer:', 'Answer:')
    packet_text = packet_text.replace('Anser:', 'Answer:')
    packet_text = packet_text.replace('Answr:', 'Answer:')
    packet_text = packet_text.replace('FTPE', 'For 10 points each')
    packet_text = packet_text.replace('FTP', 'For 10 points')
    packet_text = regex.sub(r'^TB[\.:]?', '21.', packet_text, flags=regex.IGNORECASE | regex.MULTILINE)
    packet_text = regex.sub(r'^Tiebreaker\.?', '21.', packet_text, flags=regex.IGNORECASE | regex.MULTILINE)
    packet_text = regex.sub(r'ten\spoints', '10 points', packet_text)
    packet_text = regex.sub(r'\(\d{1,2}\)', '1.', packet_text)
    packet_questions = regex.findall(REGEX_QUESTION, packet_text, flags=regex.IGNORECASE | regex.MULTILINE)

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
            question = regex.findall(REGEX_TOSSUP_TEXT, remove_formatting(tossup), flags=regex.IGNORECASE | regex.MULTILINE)[0].strip().replace('\n', ' ')
        except:
            print("TOSSUP ERROR:", tossup)
            exit(1)
        data['tossups'].append({'question': question})

        answer = regex.findall(REGEX_TOSSUP_ANSWER, tossup, flags=regex.IGNORECASE | regex.MULTILINE)[0].strip().replace('\n', ' ')
        if answer.startswith(':'):
            answer = answer[1:].strip()

        if FORMATTED_ANSWERLINE:
            data['tossups'][i]['answer_formatted'] = answer.replace('{bu}', '<b><u>').replace('{/bu}', '</u></b>').replace('{u}', '<u>').replace('{/u}', '</u>')
            answer = remove_formatting(answer)

        data['tossups'][i]['answer'] = answer

        if HAS_CATEGORY_TAGS:
            j = regex.findall(REGEX_CATEGORY_TAG, remove_formatting(tossup), flags=regex.IGNORECASE | regex.MULTILINE)[0].strip().replace('\n', ' ')
            cat = get_subcategory(j)
            if len(cat) == 0:
                print(i+1, 'tossup - ERROR: unrecognized subcategory', j)
            else:
                data['tossups'][i]['subcategory'] = cat
                data['tossups'][i]['category'] = subcat_to_cat[cat]

    for i, bonus in enumerate(bonuses):
        try:
            leadin = regex.findall(REGEX_BONUS_LEADIN, remove_formatting(bonus), flags=regex.IGNORECASE | regex.MULTILINE)[0].strip().replace('\n', ' ')
        except:
            print("BONUS ERROR:", bonus)
            exit(1)
        data['bonuses'].append({'leadin': leadin})

        data['bonuses'][i]['parts'] = []
        parts = regex.findall(REGEX_BONUS_PARTS, remove_formatting(bonus), flags=regex.IGNORECASE | regex.MULTILINE)
        for part in parts:
            part = part.strip().replace('\n', ' ')
            part = part
            data['bonuses'][i]['parts'].append(part)

        bonus = bonus + '\n[10]'
        data['bonuses'][i]['answers'] = []
        if FORMATTED_ANSWERLINE:
            data['bonuses'][i]['answers_formatted'] = []

        answers = regex.findall(REGEX_BONUS_ANSWERS, bonus, flags=regex.IGNORECASE | regex.MULTILINE)
        for answer in answers:
            answer = answer.strip().replace('\n', ' ')
            if answer.startswith(':'):
                answer = answer[1:].strip()
            if FORMATTED_ANSWERLINE:
                data['bonuses'][i]['answers_formatted'].append(answer.replace('{bu}', '<b><u>').replace('{/bu}', '</u></b>').replace('{u}', '<u>').replace('{/u}', '</u>'))
                answer = answer.replace('{bu}', '').replace('{/bu}', '').replace('{u}', '').replace('{/u}', '')
            data['bonuses'][i]['answers'].append(answer)
        bonus = bonus[:-5]

        if HAS_CATEGORY_TAGS:
            j = regex.findall(REGEX_CATEGORY_TAG, remove_formatting(bonus), flags=regex.IGNORECASE | regex.MULTILINE)[0].strip().replace('\n', ' ')
            cat = get_subcategory(j)
            if len(cat) == 0:
                print(i+1, 'bonus - ERROR: unrecognized subcategory', j)
            else:
                data['bonuses'][i]['subcategory'] = cat
                data['bonuses'][i]['category'] = subcat_to_cat[cat]

    time_now = time.perf_counter()

    if not HAS_CATEGORY_TAGS:
        for tossup in data['tossups']:
            category, subcategory = classify_question(tossup['question'], is_tossup=True)
            tossup['category'] = category
            tossup['subcategory'] = subcategory

        for i, bonus in enumerate(data['bonuses']):
            if 'parts' not in bonus:
                print(i+1, 'bonus - ERROR: no parts found for bonus')
                continue
            if len(bonus['parts']) < 3:
                print(i+1, 'bonus - ERROR: has fewer than 3 parts')
                continue
            category, subcategory = classify_question(bonus['leadin'] + bonus['parts'][0] + bonus['parts'][1] + bonus['parts'][2], is_tossup=False)
            bonus['category'] = category
            bonus['subcategory'] = subcategory

        print(f'it took {time.perf_counter() - time_now} seconds to classify')

    json.dump(data, g)