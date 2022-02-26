import os
import json

directory = 'output'

for (dirpath, dirnames, filenames) in os.walk("packets_classify"):
    count_tu = 0
    count_tu_cat = 0
    count_bonuses = 0
    count_bonuses_cat = 0

    for filename in filenames:
        if filename == '.DS_Store':
            continue

        f = open(dirpath + '/' + filename)

        data = json.load(f)

        if 'tossups' in data:
            for tu in data['tossups']:
                count_tu += 1
                if 'category' in tu:
                    count_tu_cat += 1

        if 'bonuses' in data:
            
            for tu in data['bonuses']:
                count_bonuses += 1
                if 'category' in tu:
                    count_bonuses_cat += 1

    if count_tu_cat == 0 or count_bonuses_cat == 0:
    # if count_tu == 0 or count_bonuses == 0:
        print(dirpath)
        print(f'{count_tu_cat}/{count_tu} tossups have categories')
        print(f'{count_bonuses_cat}/{count_bonuses} bonuses have categories')
