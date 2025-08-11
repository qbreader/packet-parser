# qbreader/packet-parser

A complete program to automatically parse quizbowl packets, such as from [quizbowlpackets.com](https://quizbowlpackets.com/), for use in the [qbreader/website](https://github.com/qbreader/website).

- Can also be used to parse individual packets.
- Includes a question category/subcategory classifier.
- Designed to work well with a variety of packet formats - can parse packets "as-is".

**WARNING:** Although the program can parse pdf files, results may vary - pdf parsing is notoriously inconsistent.

## How to Use

Make sure you have python3 and pip installed on your computer.

1. Clone the repository and cd into the folder.
2. Install necessary python libraries with `pip install -r requirements.txt`.
3. Download the packets, either manually or using `download-set.sh`. You need `wget` for this script.

   - If the packets are `.docx` files, then place the packets in a folder called `p-docx`.
   - If the packets are `.pdf` files, then place the packets in a folder called `p-pdf`.
   - If the packets are `.txt` files, then place the packets in a folder called `packets`.

4. If the packets are `.docx` or `.pdf` files, then run the `to-txt.sh` file to convert them to `.txt` files.
5. Run the `packet-parser.py` python file.
   Specify the `-m` flag if you want to output in a format compatible with [MODAQ](https://github.com/alopezlago/MODAQ).
   Specify the `-b` flag if you want to output in a format compatible with [buzzpoints](https://github.com/JemCasey/buzzpoint-migrator).
   - The script will prompt you if the packets have category tags.
     You can check by seeing if there are tags that look like one of the following in the packets:
     (If unsure, reply with "n").
     - \<Science - Biology\>
     - \<Biology\>
     - \<Ed. Wu - Biology\>
     - \<GW - Science, Biology\>
   - If any errors appear during the text -> json step, delete the `output/` folder, fix any mistakes in `packets/`, and run `packet-parser.py`.

### Command Line Options

You can more info by running `python packet-parser.py --help`.
Here are some common flags/options:

- `-b, --buzzpoint`:
  Output in a format compatible with [buzzpoints](https://github.com/JemCasey/buzzpoint-migrator).
- `-m, --modaq`:
  Output in a format compatible with **MODAQ**.
- `-p, --auto-insert-powermarks`:
  Insert powermarks for questions that are bolded in power but do not have an explicit powermark.
  Most useful for old Chicago Open packets.
- `-s, --space-powermarks`:
  Ensure powermarks (\*) are surrounded by spaces.
  MODAQ and qbreader both expect this for powers to correctly register.
- `-e, -l, --bonus-length INTEGER [default: 3]`:
  The number of parts in a bonus.
  Useful when you don't have 3-part bonuses (e.g. MUSES).

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

This repository includes a classifier located in the `classifier/` directory, which is a Naive Bayes classifier that uses [additive smoothing](https://en.wikipedia.org/wiki/Additive_smoothing) controlled by $\epsilon$, the smoothing parameter.
The default value of $\epsilon$ is $0.01$.

### Performance

**Methodology:** The data was shuffled using numpy with a set seed of `0`, and the split into an 80/20 train/test split.
Below is the accuracy and time[^2] for a 20% test set:

```
Naive Bayes accuracy / time:  85.35% (46053/53955) / 19.45 seconds (0.360 milliseconds per question)
```

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
