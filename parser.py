import json
import os
import regex


def get_subcategory(s):
    category = ''
    for key in subcat:
        works = True
        for word in key.split():
            if word not in s:
                works = False
                break
        if works:
            category = key
            break

    return category


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
    "British History": "History",
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

for num, file in enumerate(os.listdir(input_directory)):
    f = open(input_directory + file)
    g = open(output_directory + str(num + 1) + '.json', 'w')
    data = {
        "tossups": [],
        "bonuses": []
    }

    packet_text = ''

    for line in f.readlines():
        packet_text += line

    packet_text = packet_text.replace('\n', ' ')
    tossups, bonuses = regex.split(
        '[Bb][Oo][Nn][Uu][Ss][Ee]?[Ss]?', packet_text)
    bonuses = '>' + bonuses

    for i in regex.findall(r'(?<=\d{1,2}\. ).*?(?= [Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]:)', tossups):
        data['tossups'].append({'question_sanitized': i})

    for i, j in enumerate(regex.findall(r'(?<=[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]: ).*?(?=<.*>)', tossups)):
        data['tossups'][i]['answer_sanitized'] = j

    for i, j in enumerate(regex.findall(r'<.*?>', tossups)):
        cat = get_subcategory(j)
        if len(cat) == 0:
            print(i, "tossup error finding the subcategory", j)
        else:
            data['tossups'][i]['subcategory'] = cat
            data['tossups'][i]['category'] = subcat[cat]

    for i in regex.findall(r'(?<=> \d{1,2}\. ).*?(?= \[[10hmeHME]+\])', bonuses):
        data['bonuses'].append({'leadin_sanitized': i})

    for i, j in enumerate(regex.findall(r'(?<=[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]?: ).*?(?= \[[10hmeHME]+\]|<.*>)', bonuses)):
        if i % 3 == 0:
            data['bonuses'][i//3]['answers_sanitized'] = [j]
        else:
            data['bonuses'][i//3]['answers_sanitized'].append(j)

    for i, j in enumerate(regex.findall(r'(?<=\[[10hmeHME]+\] ).*?(?= [Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]?:)', bonuses)):
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
