from pdf2docx import Converter
import sys

pdf_file = sys.argv[1]
cv = Converter(pdf_file)
cv.convert(pdf_file.replace(".pdf", ".docx"))
cv.close()
