# qbreader/packet-parser

A complete program to automatically download and parse a set of packets from [quizbowlpackets.com](https://quizbowlpackets.com/) for use in the qbreader/website.
Can also be used to parse individual packets.
Includes a question category/subcategory classifier.
Designed to work well with a variety of packet formats - can parse packets "as-is".

**WARNING:** Although the program can parse pdf files, results may vary - pdf parsing is notoriously inconsistent.

## How to Use

Make sure you have python3 installed on your computer.

1. Clone the repository and cd into the folder.
2. Install pdf2docx, regex, and python-docx with `pip install -r requirements.txt`.
3. Run the command `./get-set.sh` (equivalent to calling `bash get-set.sh`).
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
5. If any errors appear during the text->json step, delete the `output/` folder, fix any mistakes in `packets/`, and run `parser.py -f`. **If you specified txt files when running ./get-set.sh, do not include the -f flag.**
    - The -f flag tells the parser to look for the following sequences: {bu}, {/bu}, {u}, {/u} which indicate where in the answerline there should be bolding/underlining.

## Preprocessing

If the bonus parts don't have the [10] in front of them, try adding them by matching using one of the two regexes below:
```re
(?=^[^(].*\nANSWER:)
(?=^[^0-9].*\nANSWER:)
```

## Postprocessing Packet Names

Remove first 7 characters from each file name:
```bash
cd output
for f in *; do mv "$f" "${f:6}"; done
```

Rename files from x.json to 0x.json:
```bash
cd output
for f in *; do if [ ${#f} = 6 ] ; then mv "$f" "0${f}"; fi; done
```

## Classifier

This repository includes a classifier located in the `classifier/` directory, which is a modified Naive Bayes classifier that uses a modified version of normalized hhi.
In particular, the formula used is
$$
\argmax_{y \in \text{subcats}} f(\text{word}) P(\text{word} | y)
$$

where the factor f is given as the 4th power of the [normalized hhi](https://en.wikipedia.org/wiki/Herfindahl–Hirschman_index#Formula) of the counts of the word in all 20 categories.

### Performance

I benchmarked this model against a vanilla Naive Bayes classifier.
The two models have a similar accuracy and confusion matrix, but I chose the modified model due to its speed.

**Methodology:** The data was shuffled using numpy with a set seed, and the split into an 80/20 train/test split.
Below is the accuracy and time[^1] for a 20% test set of each type of classifier.
```
HHI accuracy / time:         71.32% (23702/33234) / 11.44 seconds
Naive Bayes accuracy / time: 67.27% (22358/33234) / 66.06 seconds
```

## QuizDB

The QuizDB folder contains appropriate files to convert questions from the QuizDB JSON format to the QB Reader format.
Not recommended since most questions on QuizDB are not particularly well formatted and it may introduce a [high amount of load on the QuizDB server](https://www.quizdb.org/about#:~:text=%5BNOT%20RECOMMENDED%20EXCEPT,year%2C%20or%20tournament.).

1) Make a [QuizDB query](https://www.quizdb.org/) by selecting a tournament, clearing all other fields, and pressing search.
2) Click the JSON button and move the downloaded file to the quizdb folder.
3) Run quizdb-process.py.
4) Run change_cat_names.py.

## Background:

I needed a way to automatically download and parse packets for [QB Reader](https://www.qbreader.org/).
I wrote this program after running into issues with formatting requirements and lack of category support when using, [YAPP](https://github.com/alopezlago/YetAnotherPacketParser).
YAPP is awesome and powers an awesome moderation tool, [MODAQ](https://www.quizbowlreader.com/demo.html).

[^1]: The amount of time it took to classify all of the test samples.
