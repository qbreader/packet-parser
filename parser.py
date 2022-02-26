import json
import os
import regex
import time

has_category_tags = False

input_directory = 'packets/'
output_directory = 'output/'
os.mkdir(output_directory)


with open('subcat_conversion.json') as f:
    subcat_conversion = json.load(f)

with open('subcat.json') as f:
    subcat = json.load(f)


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


def classify_question(text, is_tossup, max_number_to_check=100000, training_directory="packets_classify"):
    i = 0
    text = set(text.split())
    text = set([word for word in text if len(word) > 4])

    best_questions = []
    for (dirpath, dirnames, filenames) in os.walk(training_directory):
        for filename in filenames:
            if filename == '.DS_Store':
                continue

            f = open(dirpath + '/' + filename)

            try:
                data = json.load(f)
            except:
                print(dirpath + '/' + filename)

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

    packet_text = packet_text.replace('\n', ' ')
    packet_text = packet_text.replace('', ' ')
    tossups, bonuses = regex.split('[Bb][Oo][Nn][Uu][Ss][Ee][Ss]', packet_text)
    # tossups, bonuses = regex.split('[Bb][Oo][Nn][Uu][Ss][Ee][Ss]', packet_text)[0], ''

    if has_category_tags:
        bonuses = '>' + bonuses
    else:
        tossups += ' 21.'
        bonuses += ' [10]'

    for i in regex.findall(r'(?<=\d{1,2}\. +|TB\. +|Tiebreaker\. +|TIEBREAKER\. +).+?(?= *[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]:)', tossups):
        data['tossups'].append({'question': i})
    print('Processed', len(data['tossups']), 'tossups')

    if has_category_tags:
        for i, j in enumerate(regex.findall(r'(?<=[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]: +).+?(?= *<.*>)', tossups)):
            data['tossups'][i]['answer'] = j
    else:
        for i, j in enumerate(regex.findall(r'(?<=[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]: +).+?(?= *\d{1,2}\.| *TB\.| *Tiebreaker\.| *TIEBREAKER\.)', tossups)):
            data['tossups'][i]['answer'] = j

    for i, j in enumerate(regex.findall(r'<.*?>', tossups)):
        cat = get_subcategory(j)
        if len(cat) == 0:
            print(i+1, "tossup error finding the subcategory", j)
        else:
            data['tossups'][i]['subcategory'] = cat
            data['tossups'][i]['category'] = subcat[cat]


    if has_category_tags:
        for i in regex.findall(r'(?<=> *\d{1,2}\. *|TB\. *|Tiebreaker\. *|TIEBREAKER\. *|Extra\. *).+?(?= *\[[10hmeHME]+\])', bonuses):
            data['bonuses'].append({'leadin': i})
    else:
        for i in regex.findall(r'(?<= +\d{1,2}\. +|TB\. +|Tiebreaker\. +|TIEBREAKER\. +|Extra\. +).+?(?= *\[[10hmeHME]+\])', bonuses):
            data['bonuses'].append({'leadin': i})
            print(i)
    print('Processed', len(data['bonuses']), 'bonuses')

    if has_category_tags:
        for i, j in enumerate(regex.findall(r'(?<=[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]?: *).+?(?= *\[[10hmeHME]+\]|<.*>)', bonuses)):
            if i % 3 == 0:
                data['bonuses'][i//3]['answers'] = [j]
            else:
                data['bonuses'][i//3]['answers'].append(j)
    else:
        for i, j in enumerate(regex.findall(r'(?<=[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]?: +).+?(?= *\[[10hmeHME]+\]| *\d{1,2}\.)', bonuses)):
            if i % 3 == 0:
                data['bonuses'][i//3]['answers'] = [j]
            else:
                data['bonuses'][i//3]['answers'].append(j)

    for i, j in enumerate(regex.findall(r'(?<=\[[10hmeHME]+\] +).+?(?= *[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]?:)', bonuses)):
        if i % 3 == 0:
            data['bonuses'][i//3]['parts'] = [j]
        else:
            data['bonuses'][i//3]['parts'].append(j)

    for i, j in enumerate(regex.findall(r'<.*?>', bonuses)):
        cat = get_subcategory(j)
        if len(cat) == 0:
            print(i+1, "bonus error finding the subcategory", j)
        else:
            data['bonuses'][i]['subcategory'] = cat
            data['bonuses'][i]['category'] = subcat[cat]

    time_now = time.perf_counter()

    if not has_category_tags:
        for bonus in data['bonuses']:
            category, subcategory = classify_question(bonus['leadin'] + bonus['parts'][0] + bonus['parts'][1] + bonus['parts'][2], is_tossup=False)
            bonus['category'] = category
            bonus['subcategory'] = subcategory

            print(category, subcategory)

        for tossup in data['tossups']:
            category, subcategory = classify_question(tossup['question'], is_tossup=True)
            tossup['category'] = category
            tossup['subcategory'] = subcategory

            print(category, subcategory)

    print(f'it took {time.perf_counter() - time_now} seconds to classify')
    json.dump(data, g)