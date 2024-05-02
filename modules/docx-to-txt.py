# Converts a docx file to a txt file while annotating the bold, italic, and underlined parts (and no other styling).

import docx
import sys


def parse_paragraph(paragraph: docx.text.paragraph.Paragraph) -> str:
    text = ""
    for runs in paragraph.runs:
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

    return text


file = sys.argv[1]
document = docx.Document(file)

for item in document.iter_inner_content():
    if isinstance(item, docx.text.paragraph.Paragraph):
        print(parse_paragraph(item))
        continue
    else:
        for row in item.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    print(parse_paragraph(paragraph))
