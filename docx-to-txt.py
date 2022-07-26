# Converts a docx file to a txt file while annotating the bold and underlined parts (and no other styling).

from docx import Document
import sys

document = Document(sys.argv[1])
for para in document.paragraphs:
    text = ''
    for runs in para.runs:
        if runs.bold and runs.underline:
            text += '{bu}' + runs.text + '{/bu}'

        elif runs.underline:
            text += '{u}' + runs.text + '{/u}'

        else:
            text += runs.text
    
    print(text)