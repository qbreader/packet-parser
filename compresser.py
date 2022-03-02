import os
import json

def removePunctuation(s, punctuation='''.,!-;:'"\/?@#$%^&*_~'''):
    return ''.join(ch for ch in s if ch not in punctuation)


with open('stop_words.txt') as f:
    stop_words = set(f.readlines())
    stop_words = set([word.strip() for word in stop_words])


for (dirpath, dirnames, filenames) in os.walk("packets_classify"):
    for filename in filenames:
        if filename == '.DS_Store':
            continue

        print(dirpath + '/' + filename)
        f = open(dirpath + '/' + filename)
        data = json.load(f)

        g = open(dirpath + '/' + filename, 'w')

        for tu in data['tossups']:
            text = set(tu['question'].split())
            text = [removePunctuation(word).lower() for word in text]
            text = [word for word in text if word not in stop_words]

            tu['question'] = text

        if 'bonuses' in data:
            for bonus in data['bonuses']:
                if 'leadin' not in bonus: continue
                if 'parts' not in bonus or len(bonus['parts']) < 3: continue

                text = bonus['leadin'] + ' ' + bonus['parts'][0] + ' ' + bonus['parts'][1] + ' ' + bonus['parts'][2]
                text = set(text.split())
                text = [removePunctuation(word).lower() for word in text]
                text = [word for word in text if word not in stop_words]

                bonus['leadin'] = text

        json.dump(data, g)
