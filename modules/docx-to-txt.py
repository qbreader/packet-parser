# Converts a docx file to a txt file while annotating the bold, italic, and underlined parts (and no other styling).

from docx import Document
import sys

document = Document(sys.argv[1])
for para in document.paragraphs:
    text = ""
    for runs in para.runs:
        if len(runs.text.strip()) == 0:
            text += runs.text
            continue

        run = runs.text

        if runs.underline:
            run = "{u}" + run + "{/u}"

        if runs.bold:
            run = "{b}" + run + "{/b}"

        if runs.italic:
            run = "{i}" + run + "{/i}"

        text += run

    print(text)
