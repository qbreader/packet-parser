# qb-packet-parser

## How to Use

Make sure you have python3 installed on your computer.

1. Clone the repository and cd into the folder.
2. Run `pip install -r requirements.txt`, which will install pdf2docx, regex, and python-docx.
3. Run the command `./get_set.sh` (equivalent to calling `bash get_set.sh`). 
If you are interested in a **non-high school** set, use one of the flags below:
    - -c = collegiate
    - -m = middle school
    - -t = trash
4. Packets will automatically be downloaded and parsed and appear in the folder `output/`. 
The script will prompt you if the packets have category tags.
You can check by seeing if there are tags that look like one of the following in the packets: 
(If unsure, reply with "n").
```
<Science - Biology>
<Biology>
<Ed. Wu - Biology>
<GW - Science, Biology>
```
5. If any errors apeear text->json step, delete the `output/` folder, fix any mistakes in `packets/`, and run `parser.py -f`. **If you specified txt files, do not include the -f flag.**
    - The -f flag tells the parser to look for the following sequences: {bu}, {/bu}, {u}, {/u} which indicate where in the answerline there should be bolding/underlining.

## Preprocessing

If the bonus parts don't have the [10] in front of them, try adding them by matching using one of the two regexes below:
```re
(?=^[^(].*\nANSWER:)
(?=^[^0-9].*\nANSWER:)
```

## Background:

I wrote this program after being dissatisfied with yet another packet parser, [YAPP](https://github.com/alopezlago/YetAnotherPacketParser), due to its strict formatting requirements and lack of category support. 
YAPP is awesome and powers an awesome moderation tool, [MODAQ](https://www.quizbowlreader.com/demo.html).
