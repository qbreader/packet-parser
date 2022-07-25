# Converts a docx file to a txt file while annotating the bold and underlined parts (and no other styling).

from docx import Document
import sys

document = Document(sys.argv[1])
text = ''
for para in document.paragraphs:
    for runs in para.runs:
        if runs.bold and runs.underline:
            text += '<u><b>' + runs.text + '</b></u>'

        elif runs.underline:
            text += '<u>' + runs.text + '</u>'
        
        else:
            text += runs.text
    
    text += '\n'

print(text)