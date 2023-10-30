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

5. If any errors appear during the text->json step, delete the `output/` folder, fix any mistakes in `packets/`, and run `packet-parser.py -f`. **If you specified txt files when running ./get-set.sh, do not include the -f flag.**
   - The -f flag tells the parser to look for the following sequences: {b}, {/b}, {u}, {/u}, {i}, {/i}, which indicate where in the answerline there should be bolding/underlining/italics.

## Errors

When running the packet parser, it's possible that you'll run into WARNINGS and ERRORS. This is due to errors in formatting of the packets. Common errors include:

- WARNING: tossup `{question #}` answer may contain the next question
- WARNING: bonus `{question #}` leadin may contain the previous question
  - These two errors likely means that you're missing a question number. Try adding a 1. in front of the next question.
- ERROR: bonus `{question #}` has fewer than `{EXPECTED_BONUS_LENGTH}` parts
  - This likely means you're missing a [10] somewhere, or it's mistyped (such as [10[)

## Preprocessing

If the bonus parts don't have the [10] in front of them, try adding them by matching using one of the two regexes below:

```re
(?=^[^(].*\nANSWER:)
(?=^[^0-9].*\nANSWER:)
```

## Postprocessing Packet Names

**UPDATE:** I now recommend using the [Batch Rename](https://marketplace.visualstudio.com/items?itemName=JannisX11.batch-rename-extension) extension for VSCode and using multiline editing to rename the files.

Although most modern file explorers (including VS Code) are smart enough to figure out the order of the packet numbers to order the number part numerically, the program to upload the packets is not.
Instead, they order them lexically, like so:

```
Packet 1.json
Packet 10.json
Packet 11.json
Packet 12.json
Packet 2.json
Packet 3.json
Packet 4.json
Packet 5.json
Packet 6.json
Packet 7.json
Packet 8.json
Packet 9.json
```

It's a good idea to add 0's in front of all the single-digit names to make sure that they are ordered correctly.
Furthermore, it's a good idea to remove the "Packet" part of all the names or any other redundant info (such as set names), since they're unnecessary.
Generally speaking, this includes phrases that appear in every packet name, and does NOT include the list of schools that wrote the packet (which is commonly the case for ACF packets).
The final result will look like this:

```
01.json
02.json
03.json
04.json
05.json
06.json
07.json
08.json
09.json
10.json
11.json
12.json
```

Remove first 7 characters from each file name:

```bash
cd output
for f in *; do mv "$f" "${f:7}"; done
```

Rename files from x.json to 0x.json:[^1]

```bash
cd output
for f in *; do if [ ${#f} = 6 ] ; then mv "$f" "0${f}"; fi; done
```

## Classifier

This repository includes a classifier located in the `classifier/` directory, which is a modified Naive Bayes classifier.
In particular, the formula used is

$$
\argmax_{y \in S} \sum_{\text{word} \in W} \ln(P(\text{word} | y) + \epsilon)
$$

where $S$ is the set of subcategories and $W$ is the set of words in the question that are not in the `stop-words.txt` list.
Note that this differs from the Naive Bayes formula in that the (class) priors are not included.

$\epsilon$ is a smoothing parameter (to avoid taking the natural log of 0), and is equal to $0.00001$.

### Performance

**Methodology:** The data was shuffled using numpy with a set seed of `0`, and the split into an 80/20 train/test split.
Below is the accuracy and time[^2] for a 20% test set:

```
Modified Naive Bayes accuracy / time:  82.10% (26818/32667) / 19.42 seconds
```

Some more results:

**Note:** `set` refers to calling the python `set` function on the list of tokens

- `set` on prediction, no `set` on generation: 26572
- no `set` on prediction, no `set` on generation: 26639
- no `set` on prediction, `set` on generation: 26624
- `set` on prediction, `set` on generation: 26550

| epsilon  | values |
| -------- | ------ |
| 0.0001   | 26681  |
| 0.00001  | 26818  |
| 0.000001 | 26807  |

## QuizDB

**UPDATE:** As of November 28th, 2022, [QuizDB has been shut down](https://hsquizbowl.org/forums/viewtopic.php?t=26489).
[nocard.org](https://nocard.org) is the closest replacement, but it does not support exporting questions to text, csv, or json.

The QuizDB folder contains appropriate files to convert questions from the QuizDB JSON format to the QB Reader format.
Not recommended since most questions on QuizDB are not particularly well formatted and it may introduce a [high amount of load on the QuizDB server](https://www.quizdb.org/about#:~:text=%5BNOT%20RECOMMENDED%20EXCEPT,year%2C%20or%20tournament.).

1. Make a [QuizDB query](https://www.quizdb.org/) by selecting a tournament, clearing all other fields, and pressing search.
2. Click the JSON button and move the downloaded file to the quizdb folder.
3. Run `quizdb-process.py`.
4. Run `change_cat_names.py`.

## Background:

I needed a way to automatically download and parse packets for [QB Reader](https://www.qbreader.org/).
I wrote this program after running into issues with formatting requirements and lack of category support when using [YAPP](https://github.com/alopezlago/YetAnotherPacketParser).
YAPP is awesome and powers an awesome moderation tool, [MODAQ](https://www.quizbowlreader.com/demo.html).

[^1]: The number 6 comes from the fact that the length of `x.json` is 6 characters long. Modify as you please for other extensions and use cases.
[^2]: The amount of time it took to classify all of the test samples.
