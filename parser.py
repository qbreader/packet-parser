import json
import os
import regex


def get_subcategory(s):
    category = ''
    for key in subcat_conversion:
        works = True
        for word in key.split():
            if word not in s:
                works = False
                break
        if works:
            category = subcat_conversion[key]
            break

    return category


subcat_conversion = {
    "American Lit": "American Literature",
    "American Literature": "American Literature",
    "US Literature": "American Literature",
    "British Lit": "British Literature",
    "British Literature": "British Literature",
    "Classical Literature": "Classical Literature",
    "European/World Lit": "European Literature",
    "European Literature": "European Literature",
    "World Literature": "World Literature",
    "Other Literature": "Other Literature",
    "Other Lit": "Other Literature",
    "Literature": "Other Literature",
    "Drama": "Drama",
    "Poetry": "Poetry",
    "Long Fiction": "Long Fiction",
    "Long Form": "Long Fiction",
    "Short Fiction": "Short Fiction",
    "Short Form": "Short Fiction",
    "Misc Literature": "Misc Literature",
    "Miscellaneous Literature": "Misc Literature",
    "American History": "American History",
    "US Hist": "American History",
    "US History": "American History",
    "Ancient History": "Ancient History",
    "British History": "European History",
    "Commonwealth History": "European History",
    "European History": "European History",
    "Euro History": "European History",
    "Other Western History": "European History",
    "World History": "World History",
    "Misc. History": "Other History",
    "Zeitgeist": "Other History",
    "Other History": "Other History",
    "Historiography": "Other History",
    "Archaeology": "Other History",
    "Bio": "Biology",
    "Biology": "Biology",
    "Chem": "Chemistry",
    "Chemistry": "Chemistry",
    "Phys": "Physics",
    "Physics": "Physics",
    "Math": "Math",
    "Mathematics": "Math",
    "Astronomy": "Other Science",
    "Computer Science": "Other Science",
    "Earth Science": "Other Science",
    "Engineering": "Other Science",
    "Other Science": "Other Science",
    "Other Sci": "Other Science",
    "Painting": "Visual Fine Arts",
    "Sculpture": "Visual Fine Arts",
    "Visual FA": "Visual Fine Arts",
    "Visual Fine Arts": "Visual Fine Arts",
    "Visual Arts": "Visual Fine Arts",
    "Music": "Auditory Fine Arts",
    "Auditory FA": "Auditory Fine Arts",
    "Auditory Fine Arts": "Auditory Fine Arts",
    "Auditory Arts": "Auditory Fine Arts",
    "Misc. FA": "Other Fine Arts",
    "Other Arts": "Other Fine Arts",
    "Architecture": "Other Fine Arts",
    "Photography": "Visual Fine Arts",
    "Film": "Other Fine Arts",
    "Jazz": "Auditory Fine Arts",
    "Opera": "Other Fine Arts",
    "Dance": "Other Fine Arts",
    "Religion": "Religion",
    "Myth": "Mythology",
    "Mythology": "Mythology",
    "Philosophy": "Philosophy",
    "Economics": "Social Science",
    "Psychology": "Social Science",
    "Linguistics": "Social Science",
    "Sociology": "Social Science",
    "Anthropology": "Social Science",
    "Other Social Science": "Social Science",
    "Social Science": "Social Science",
    "Current Events": "Current Events",
    "Geography": "Geography",
    "Other Academic": "Other Academic",
    "Mixed Academic": "Other Academic",
    "Trash": "Trash",
    "Pop Culture": "Trash",
    "Sports": "Trash",
}

subcat = {
    "American Literature": "Literature",
    "British Literature": "Literature",
    "Classical Literature": "Literature",
    "European Literature": "Literature",
    "World Literature": "Literature",
    "Other Literature": "Literature",
    "Drama": "Literature",
    "Poetry": "Literature",
    "Long Fiction": "Literature",
    "Short Fiction": "Literature",
    "Misc Literature": "Literature",
    "American History": "History",
    "Ancient History": "History",
    "European History": "History",
    "World History": "History",
    "Other History": "History",
    "Historiography": "History",
    "Archaeology": "History",
    "Biology": "Science",
    "Chemistry": "Science",
    "Physics": "Science",
    "Math": "Science",
    "Astronomy": "Science",
    "Computer Science": "Science",
    "Earth Science": "Science",
    "Engineering": "Science",
    "Other Science": "Science",
    "Painting": "Fine Arts",
    "Sculpture": "Fine Arts",
    "Music": "Fine Arts",
    "Other Arts": "Fine Arts",
    "Architecture": "Fine Arts",
    "Photography": "Fine Arts",
    "Film": "Fine Arts",
    "Jazz": "Fine Arts",
    "Opera": "Fine Arts",
    "Dance": "Fine Arts",
    "Visual Fine Arts": "Fine Arts",
    "Auditory Fine Arts": "Fine Arts",
    "Other Fine Arts": "Fine Arts",
    "Religion": "Religion",
    "Mythology": "Mythology",
    "Philosophy": "Philosophy",
    "Economics": "Social Science",
    "Psychology": "Social Science",
    "Linguistics": "Social Science",
    "Sociology": "Social Science",
    "Anthropology": "Social Science",
    "Other Social Science": "Social Science",
    "Social Science": "Social Science",
    "Current Events": "Current Events",
    "Geography": "Geography",
    "Other Academic": "Other Academic",
    "Trash": "Trash",
}

input_directory = 'packets/'
output_directory = 'output/'
os.mkdir(output_directory)

for file in os.listdir(input_directory):
    if file == '.DS_Store':
        continue
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
    bonuses = '>' + bonuses

    for i in regex.findall(r'(?<=\d{1,2}\. +|TB\. +|Tiebreaker\. +|TIEBREAKER\. +).+?(?= *[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]:)', tossups):
        data['tossups'].append({'question_sanitized': i})
    print('Processed', len(data['tossups']), 'tossups')

    for i, j in enumerate(regex.findall(r'(?<=[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]: +).+?(?= *<.*>)', tossups)):
        data['tossups'][i]['answer_sanitized'] = j

    for i, j in enumerate(regex.findall(r'<.*?>', tossups)):
        cat = get_subcategory(j)
        if len(cat) == 0:
            print(i, "tossup error finding the subcategory", j)
        else:
            data['tossups'][i]['subcategory'] = cat
            data['tossups'][i]['category'] = subcat[cat]

    for i in regex.findall(r'(?<=> *\d{1,2}\. +|TB. +|Tiebreaker. +|TIEBREAKER\. +).+?(?= +\[[10hmeHME]+\])', bonuses):
        data['bonuses'].append({'leadin_sanitized': i})

    print('Processed', len(data['bonuses']), 'bonuses')

    for i, j in enumerate(regex.findall(r'(?<=[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]?: +).+?(?= *\[[10hmeHME]+\]|<.*>)', bonuses)):
        if i % 3 == 0:
            data['bonuses'][i//3]['answers_sanitized'] = [j]
        else:
            data['bonuses'][i//3]['answers_sanitized'].append(j)

    for i, j in enumerate(regex.findall(r'(?<=\[[10hmeHME]+\] +).+?(?= *[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]?:)', bonuses)):
        if i % 3 == 0:
            data['bonuses'][i//3]['parts_sanitized'] = [j]
        else:
            data['bonuses'][i//3]['parts_sanitized'].append(j)

    for i, j in enumerate(regex.findall(r'<.*?>', bonuses)):
        cat = get_subcategory(j)
        if len(cat) == 0:
            print(i, "bonus error finding the subcategory", j)
        else:
            data['bonuses'][i]['subcategory'] = cat
            data['bonuses'][i]['category'] = subcat[cat]

    json.dump(data, g)
