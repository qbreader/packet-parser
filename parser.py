import json
import os
import regex
import time

has_category_tags = True

input_directory = 'packets/'
output_directory = 'output/'
os.mkdir(output_directory)


with open('subcat_conversion.json') as f:
    subcat_conversion = json.load(f)

with open('subcat.json') as f:
    subcat = json.load(f)

with open('stop_words.txt') as f:
    stop_words = set(f.readlines())
    stop_words = set([word.strip() for word in stop_words])


all_questions = []
for (dirpath, dirnames, filenames) in os.walk('packets_classify'):
    for filename in filenames:
        if filename == '.DS_Store':
            continue

        f = open(dirpath + '/' + filename)

        try:
            data = json.load(f)
        except:
            print(dirpath + '/' + filename)
            continue

        all_questions.append(data)


def removePunctuation(s, punctuation='''.,!-;:'"\/?@#$%^&*_~'''):
    return ''.join(ch for ch in s if ch not in punctuation)


def get_subcategory(s):
    for key in subcat_conversion:
        works = True
        for word in key.split():
            if word not in s:
                works = False
                break
        if works:
            return subcat_conversion[key]

    return ''


def difference(text1, text2):
    """
    Returns the number of words in common between the two words
    """
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
                best_questions.append(max(data['tossups'], key=lambda x: 0 if 'subcategory' not in x else difference(x['question'], text)))

            i += len(data['tossups'])
        elif 'bonuses' in data:
            if len(data['bonuses']) > 0:
                best_questions.append(max(data['bonuses'], key=lambda x: 0 if 'subcategory' not in x else difference(x['leadin'], text)))

            i += len(data['bonuses'])

        if i > max_number_to_check:
            break
    
    if is_tossup:
        best = max(best_questions, key=lambda x: difference(x['question'], text))
    else:
        best = max(best_questions, key=lambda x: difference(x['leadin'], text))

    return best['category'], best['subcategory']


for file in os.listdir(input_directory):
    if file == '.DS_Store': continue
    print(file)

    f = open(input_directory + file)
    g = open(output_directory + file[:-4] + '.json', 'w')

    data = {
        "tossups": [],
        "bonuses": []
    }

    packet_text = ''
    for line in f.readlines():
        packet_text += line
    
    packet_text = packet_text + '\n0.'

    packet_text = packet_text.replace('', ' ')
    packet_text = regex.sub(r'ten\spoints', '10 points', packet_text)
    packet_questions = regex.findall(r'\d{1,2}\.(?:.|\n)*?ANSWER:(?:.*\n)*?(?=\d{1,2}\.)', packet_text)

    tossups = []
    bonuses = []

    for q in packet_questions:
        if regex.findall(r'For\s10\spoints\seach', q, flags=regex.IGNORECASE) or regex.findall(r'For\s10\spoints:', q, flags=regex.IGNORECASE):
            bonuses.append(q)
        else:
            tossups.append(q)

    print('Processed', len(tossups), 'tossups')
    print('Processed', len(bonuses), 'bonuses')

    for i, tossup in enumerate(tossups):
        question = regex.findall(r'(?<=\d{1,2}\.)(?:.|\n)*?(?=ANSWER)', tossup)[0].strip().replace('\n', ' ')
        data['tossups'].append({"question": question})

        part = ''
        if has_category_tags:
            part = regex.findall(r'(?<=ANSWER:)(?:.|\n)*(?=<)', tossup)[0].strip().replace('\n', ' ')
        else:
            part = regex.findall(r'(?<=ANSWER:)(?:.|\n)*', tossup)[0].strip().replace('\n', ' ')
        
        data['tossups'][i]["answer"] = part

        if has_category_tags:
            j = regex.findall(r'<.*?>', tossup)[0].strip().replace('\n', ' ')
            cat = get_subcategory(j)
            if len(cat) == 0:
                print(i+1, "tossup error finding the subcategory", j)
            else:
                data['tossups'][i]['subcategory'] = cat
                data['tossups'][i]['category'] = subcat[cat]

    for i, bonus in enumerate(bonuses):
        leadin = regex.findall(r'(?<=\d{1,2}\.)(?:.|\n)*?(?=\[)', bonus)[0].strip().replace('\n', ' ')
        data['bonuses'].append({"leadin": leadin})

        bonus = bonus + '\n[10]'
        data['bonuses'][i]["answers"] = []
        answers = regex.findall(r'(?<=ANSWER:)(?:.|\n)*?(?=\[.{1,3}\]|<)', bonus)
        for answer in answers:
            answer = answer.strip().replace('\n', ' ')
            data['bonuses'][i]["answers"].append(answer)
        bonus = bonus[:-5]

        data['bonuses'][i]["parts"] = []
        parts = regex.findall(r'(?<=\[.{1,3}\])(?:.|\n)*?(?=ANSWER)', bonus)
        for part in parts:
            part = part.strip().replace('\n', ' ')
            data['bonuses'][i]["parts"].append(part)
        
        if has_category_tags:
            j = regex.findall(r'<.*?>', bonus, flags=regex.IGNORECASE)[0].strip().replace('\n', ' ')
            cat = get_subcategory(j)
            if len(cat) == 0:
                print(i+1, "tossup error finding the subcategory", j)
            else:
                data['bonuses'][i]['subcategory'] = cat
                data['bonuses'][i]['category'] = subcat[cat]

    time_now = time.perf_counter()

    if not has_category_tags:
        for bonus in data['bonuses']:
            if 'parts' not in bonus:
                print('No parts for bonus', bonus)
                continue
            if len(bonus['parts']) < 3:
                print('Bonus', bonus['parts'], 'has less than 3 parts')
                continue
            category, subcategory = classify_question(bonus['leadin'] + bonus['parts'][0] + bonus['parts'][1] + bonus['parts'][2], is_tossup=False)
            bonus['category'] = category
            bonus['subcategory'] = subcategory

            # print(category, subcategory)

        for tossup in data['tossups']:
            category, subcategory = classify_question(tossup['question'], is_tossup=True)
            tossup['category'] = category
            tossup['subcategory'] = subcategory

            # print(category, subcategory)

        print(f'it took {time.perf_counter() - time_now} seconds to classify')
    json.dump(data, g)