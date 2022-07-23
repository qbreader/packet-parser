# qb-packet-parser

This program uses the [poppler](https://poppler.freedesktop.org/) utilities to parse PDFs and [docx2txt](http://docx2txt.sourceforge.net/) to parse DOCX files. (Installing docx2txt may install the program as `docx2txt.sh`, in which case you'll need to rename it to `docx2txt` or change the source script.)

Run the `get_set` file to automatically download an entire set and parse it.
Flags:
- -c = collegiate
- -m = middle school
- -t = trash

If there are any issues with the parsing text to json step, delete the `output/` folder, fix any mistakes in `packets/`, and run `parser.py`.

## Background:

I wrote this program after being dissatisfied with yet another packet parser, [YAPP](https://github.com/alopezlago/YetAnotherPacketParser), due to its strict formatting requirements and lack of category support. YAPP is awesome and powers [MODAQ](https://www.quizbowlreader.com/demo.html), which I believe to be the future of quizbowl moderation.
