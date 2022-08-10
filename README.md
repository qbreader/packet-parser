# qb-packet-parser

A complete program to automatically download and parse a set of packets from quizbowlpackets.com.
Can also be used to parse individual packets.
Designed to work well with a variety of packet formats - can parse packets "as-is".

## How to Use

Make sure you have python3 installed on your computer.

1. Clone the repository and cd into the folder.
2. Install pdf2docx, regex, and python-docx with `pip install -r requirements.txt`.
3. Run the command `./get_set.sh` (equivalent to calling `bash get_set.sh`).
Packets will automatically be downloaded and parsed and appear in the folder `output/`. 
4. The script will prompt you if the packets have category tags.
You can check by seeing if there are tags that look like one of the following in the packets: 
(If unsure, reply with "n").
```
<Science - Biology>
<Biology>
<Ed. Wu - Biology>
<GW - Science, Biology>
```
5. If any errors apeear text->json step, delete the `output/` folder, fix any mistakes in `packets/`, and run `parser.py -f`. **If you specified txt files when running ./get_set.sh, do not include the -f flag.**
    - The -f flag tells the parser to look for the following sequences: {bu}, {/bu}, {u}, {/u} which indicate where in the answerline there should be bolding/underlining.

## Preprocessing

If the bonus parts don't have the [10] in front of them, try adding them by matching using one of the two regexes below:
```re
(?=^[^(].*\nANSWER:)
(?=^[^0-9].*\nANSWER:)
```

## Background:

I needed a way to automatically download and parse packets for [qbreader](https://www.qbreader.org/).
I wrote this program after running into issues with formatting requirements and lack of category support when using, [YAPP](https://github.com/alopezlago/YetAnotherPacketParser).
YAPP is awesome and powers an awesome moderation tool, [MODAQ](https://www.quizbowlreader.com/demo.html).
