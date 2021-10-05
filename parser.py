import regex
import re
import json

f = open('packet.txt')
g = open('packet.json', 'w')
data = {
    "tossups": [],
    "bonuses": []
}

s = ''

for line in f.readlines():
    s += line

s = s.replace('\n', ' ')
tossups, bonuses = re.split('[Bb][Oo][Nn][Uu][Ss][Ee]?[Ss]?', s)
bonuses = '>' + bonuses

for i in regex.findall(r'(?<=\d{1,2}\. ).*?(?= [Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]:)', tossups):
    data['tossups'].append({'question_sanitized': i})

for i, j in enumerate(regex.findall(r'(?<=[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]: ).*?(?=<.*>)', tossups)):
    data['tossups'][i]['answer_sanitized'] = j

for i in regex.findall(r'(?<=> \d{1,2}\. ).*?(?= \[[10hmeHME]+\])', bonuses):
    data['bonuses'].append({'leadin_sanitized': i})

for i, j in enumerate(regex.findall(r'(?<=[Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]?: ).*?(?= \[[10hmeHME]+\]|<.*>)', bonuses)):
    if i%3 == 0:
        data['bonuses'][i//3]['answers_sanitized'] = [j]
    else:
        data['bonuses'][i//3]['answers_sanitized'].append(j)

for i, j in enumerate(regex.findall(r'(?<=\[[10hmeHME]+\] ).*?(?= [Aa][Nn]?[Ss]?[Ww]?[Ee]?[Rr]?:)', bonuses)):
    if i%3 == 0:
        data['bonuses'][i//3]['parts_sanitized'] = [j]
    else:
        data['bonuses'][i//3]['parts_sanitized'].append(j)

json.dump(data, g)