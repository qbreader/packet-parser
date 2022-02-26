import os
import json

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
            text = [word for word in text if len(word) > 4]

            tu['question'] = text

        if 'bonuses' in data:
            for bonus in data['bonuses']:
                if 'leadin' not in bonus: continue
                if 'parts' not in bonus or len(bonus['parts']) < 3: continue

                text = bonus['leadin'] + ' ' + bonus['parts'][0] + ' ' + bonus['parts'][1] + ' ' + bonus['parts'][2]
                text = set(text.split())
                text = [word for word in text if len(word) > 4]

                bonus['leadin'] = text

        json.dump(data, g)
