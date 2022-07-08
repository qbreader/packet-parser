# qb-packet-parser

Make sure you have the [poppler](https://poppler.freedesktop.org/) utilities installed on your system.
Run the `get_set` file (using `bash get_set`) to automatically download an entire set and parse it.
Flags:
- -c = collegiate
- -m = middle school
- -t = trash

If there are any issues with the parsing text to json step, delete the `output/` folder, fix any mistakes in `packets/`, and run `parser.py`.