# Converts a docx file to a txt file while annotating the bold and underlined parts (and no other styling).

from docx import Document
import sys

document = Document(sys.argv[1])
for para in document.paragraphs:
    text = ''
    for runs in para.runs:
        run = ''
        if len(runs.text.strip()) == 0:
            run = runs.text
        elif runs.bold and runs.underline:
            run = '{bu}' + runs.text + '{/bu}'

        elif runs.underline:
            run = '{u}' + runs.text + '{/u}'

        else:
            run = runs.text

        if runs.italic:
            run = '{i}' + run + '{/i}'

        text += run

    print(text)
