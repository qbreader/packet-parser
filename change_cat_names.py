import os
import json

# convert quizdb subcats to standard subcats
subcategory_map = {
    "Fine Arts Audiovisual": "Other Fine Arts",
    "Fine Arts Auditory": "Auditory Fine Arts",
    "Fine Arts Other": "Other Fine Arts",
    "Fine Arts Opera": "Other Fine Arts",
    "Fine Arts Visual": "Visual Fine Arts",

    "History American": "American History",
    "History British": "European History",
    "History Ancient": "Ancient History",
    "History European": "European History",
    "History World": "World History",
    "History Other": "Other History",

    "Science American": "Other Science",
    "Science Biology": "Biology",
    "Science Chemistry": "Chemistry",
    "Science Computer Science": "Other Science",
    "Science Math": "Math",
    "Science Other": "Other Science",
    "Science Physics": "Physics",
    "Science World": "World Science",

    "Literature American": "American Literature",
    "Literature British": "British Literature",
    "Literature Classical": "Classical Literature",
    "Literature European": "European Literature",
    "Literature Other": "Other Literature",
    "Literature World": "World Literature",

    "Current Events American": "Current Events",
    "Current Events Other": "Current Events",
}

count = 0

for (dirpath, dirnames, filenames) in os.walk("packets_copy"):
    for filename in filenames:
        if filename == '.DS_Store':
            continue

        f = open(dirpath + '/' + filename)
        data = json.load(f)
        for tossup in data['tossups']:
            if 'subcategory' not in tossup:
                continue

            for subcategory in subcategory_map:
                if tossup['subcategory'] == subcategory:
                    tossup['subcategory'] = subcategory_map[subcategory]
                    count += 1

        if 'bonuses' not in data:
            continue

        for bonus in data['bonuses']:
            if 'subcategory' not in bonus:
                continue

            for subcategory in subcategory_map:
                if bonus['subcategory'] == subcategory:
                    bonus['subcategory'] = subcategory_map[subcategory]
                    count += 1
        
        g = open(dirpath + '/' + filename, 'w')
        json.dump(data, g)

print(f'changed {count} subcategories')
