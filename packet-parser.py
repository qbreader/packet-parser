import json
import os
import regex
import sys

from bcolors import bcolors
from classifier.classify import classify_question

# Make sure to specify both, if they are not empty strings.
# Only specifying the category will cause the program to use the question classifier.
CONSTANT_CATEGORY = ""
CONSTANT_SUBCATEGORY = ""

# Uses question classifier to assign category and subcategory
# if there are category tags, but the category in the tag is unrecognized.
CLASSIFY_UNKNOWN_CATEGORIES = True

# insert (*) powermarks for questions that are
# bolded in power but do not have an explicit powermark
AUTO_INSERT_POWERMARKS = False

EXPECTED_BONUS_LENGTH = 3

INPUT_DIRECTORY = "packets/"
OUTPUT_DIRECTORY = "output/"

########## START OF PROMPTS ##########

FORMATTED_ANSWERLINE = len(sys.argv) == 2 and sys.argv[1] == "-f"
HAS_QUESTION_NUMBERS = input("Do you have question numbers? (y/n) ") == "y"
HAS_CATEGORY_TAGS = input("Do you have category tags? (y/n) ") == "y"
print("Using category tags" if HAS_CATEGORY_TAGS else "Using question classifier")

try:
    os.mkdir(OUTPUT_DIRECTORY)
except FileExistsError:
    print(f"{bcolors.WARNING}WARNING:{bcolors.ENDC} Output directory already exists")
    if not input("Continue? (y/n) ") == "y":
        exit(0)

########## END OF PROMPTS ##########


########## START OF REGEX ##########

REGEX_FLAGS = regex.IGNORECASE | regex.MULTILINE

if HAS_QUESTION_NUMBERS and HAS_CATEGORY_TAGS:
    REGEX_QUESTION = r"^ *\d{1,2}\.(?:.|\n)*?ANSWER(?:.|\n)*?<[^>]*>"
elif HAS_QUESTION_NUMBERS:
    # REGEX_QUESTION = r"^ *\d{1,2}\.(?:.|\n)*?ANSWER(?:.*\n)*?(?= *\d{1,2}\.)"
    REGEX_QUESTION = (
        r"\d{0,2}(?:[^\d\n].*\n)*[ \t]*ANSWER.*(?:\n.+)*?(?=\n\s*\d{1,2}|\n\s*$)"
    )
else:
    REGEX_QUESTION = r"(?:[^\n].*\n)*[ \t]*ANSWER.*(?:\n.*)*?(?=\n$)"

if not HAS_CATEGORY_TAGS and (
    (not CONSTANT_CATEGORY == "") and (not CONSTANT_SUBCATEGORY == "")
):
    print(
        f"{bcolors.WARNING}WARNING:{bcolors.ENDC} using fixed category and subcategory"
    )

REGEX_CATEGORY_TAG = r"<[^>]*>"

REGEX_TOSSUP_TEXT = r"(?<=\d{1,2}\.)(?:.|\n)*?(?=^ ?ANSWER|ANSWER:)"
REGEX_TOSSUP_ANSWER = (
    r"(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*(?=<[^>]*>)"
    if HAS_CATEGORY_TAGS
    else r"(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*"
)

REGEX_BONUS_LEADIN = r"(?<=^ *\d{1,2}\.)(?:.|\n)*?(?=\[(?:10)?[EMH]?\])"
REGEX_BONUS_PARTS = r"(?<=\[(?:10)?[EMH]?\])(?:.|\n)*?(?=^ ?ANSWER|ANSWER:)"
REGEX_BONUS_ANSWERS = r"(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*?(?=\[(?:10)?[EMH]?\]|<[^>]*>)"
REGEX_BONUS_TAGS = r"(?<=\[)\d{0,2}?[EMH]?(?=\])"

########## END OF REGEX ##########


ANSWER_TYPOS = [
    "ASWER:",
    "ANWER:",
    "ANSER:",
    "ANSWR:",
    "ANSWE:",
    "ASNWER:",
    "ANSEWR:",
    "ANWSER:",
    "ANSWRE:",
    "ANSWER;",
    "AMSWER:",
    "ANSWSER:",
    "ANSWERS:",
]

TEN_TYPOS = [
    "[5]",
    "[10[",
    "]10]",
    "[10}",
    "{10]",
    "[10 ]",
    "[15]",
    "[20]",
    "[30]",
]


with open("standardize-subcats.json") as f:
    STANDARDIZE_SUBCATS = json.load(f)


with open("subcat-to-cat.json") as f:
    SUBCAT_TO_CAT = json.load(f)


def format_text(text):
    return (
        text.replace("{bu}", "<b><u>")
        .replace("{/bu}", "</u></b>")
        .replace("{b}", "<b>")
        .replace("{/b}", "</b>")
        .replace("{u}", "<u>")
        .replace("{/u}", "</u>")
        .replace("{i}", "<i>")
        .replace("{/i}", "</i>")
    )


def get_subcategory(text: str):
    text = text.lower()
    for subcat in STANDARDIZE_SUBCATS:
        works = True
        for word in regex.split(f"[\/ ]", subcat.lower()):
            if word not in text:
                works = False
                break
        if works:
            return STANDARDIZE_SUBCATS[subcat]

    return ""


def remove_formatting(text: str, include_italics=False):
    text = (
        text.replace("{bu}", "")
        .replace("{/bu}", "")
        .replace("{b}", "")
        .replace("{/b}", "")
        .replace("{u}", "")
        .replace("{/u}", "")
    )

    if not include_italics:
        text = text.replace("{i}", "").replace("{/i}", "")

    return text


def remove_punctuation(s: str, punctuation=""".,!-;:'"\/?@#$%^&*_~()[]{}“”‘’"""):
    return "".join(ch for ch in s if ch not in punctuation)


for filename in sorted(os.listdir(INPUT_DIRECTORY)):
    if filename == ".DS_Store":
        continue

    f = open(INPUT_DIRECTORY + filename)
    packet_text = ""

    for line in f.readlines():
        packet_text += line

    packet_text = packet_text + "\n0."
    # remove zero-width characters
    packet_text = packet_text.replace("", "").replace("​", "")

    packet_text = (
        packet_text.replace("\u00a0", " ")
        .replace(" {/bu}", "{/bu} ")
        .replace(" {/u}", "{/u} ")
        .replace(" {/i}", "{/i} ")
        .replace("{/bu}{bu}", "")
        .replace("{/u}{u}", "")
        .replace("{/i}{i}", "")
        .replace("{i}\n{/i}", "\n")
        .replace("{i} {/i}", " ")
        .replace("\n10]", "[10]")
        .replace("[5,5]", "[10]")
        .replace("[5/5]", "[10]")
        .replace("[5, 5]", "[10]")
        .replace("[5,5,5,5]", "[20]")
        .replace("[5/5/5/5]", "[20]")
        .replace("[10/10]", "[20]")
        .replace("[2x10]", "[20]")
        .replace("[2x5]", "[10]")
        .replace("[10 ", "[10] ")
        .replace("AUDIO RELATED BONUS: ", "\n")
        .replace("HANDOUT RELATED BONUS: ", "\n")
        .replace("RELATED BONUS: ", "\n")
        .replace("RELATED BONUS. ", "\n")
        .replace("RELATED BONUS\n", "\n\n")
        .replace("HANDOUT BONUS: ", "\n")
        .replace("BONUS: ", "\n")
        .replace("Bonus: ", "\n")
        .replace("BONUS. ", "\n")
        .replace("TOSSUP. ", "")
    )
    # .replace("\n(10)", "\n[10]")
    # .replace('FTPE', 'For 10 points each') \
    # .replace('FTP', 'For 10 points') \

    for typo in ANSWER_TYPOS:
        packet_text = packet_text.replace(typo, "ANSWER:")
        packet_text = packet_text.replace(typo.title(), "ANSWER:")

    packet_text = regex.sub(
        r"^\{(bu|b|u|i)\}(\d{1,2}|TB|X)\.", "1. {b}", packet_text, flags=REGEX_FLAGS
    )
    packet_text = regex.sub(
        r"^\(?(\d{1,2}|TB)\) ", "1. ", packet_text, flags=REGEX_FLAGS
    )
    packet_text = regex.sub(r"^TB[\.:]?", "21.", packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r"^X[\.:]?", "21.", packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r"^Tiebreaker[\.:]?", "21.", packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r"^T\d{1,2}[\.:]?", "21.", packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r"^S\d{1,2}[\.:]?", "21.", packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r"^Extra[\.:]?", "21.", packet_text, flags=REGEX_FLAGS)
    packet_text = regex.sub(r"^[ABC][.:] *", "[10] ", packet_text, flags=REGEX_FLAGS)
    # packet_text = regex.sub(r'ten\spoints', '10 points', packet_text)
    packet_text = regex.sub(r"^ *$", "", packet_text, flags=REGEX_FLAGS)

    if not HAS_CATEGORY_TAGS:
        packet_text = regex.sub(REGEX_CATEGORY_TAG, "", packet_text)

    packet_questions = regex.findall(REGEX_QUESTION, packet_text, flags=REGEX_FLAGS)

    tossups = []
    bonuses = []

    for question in packet_questions:
        isBonus = regex.findall(r"^\[(5|10|15)?[EMH]?\]", question, flags=REGEX_FLAGS)

        if (not HAS_QUESTION_NUMBERS) ^ (
            1 if regex.match("^\d{1,2}\.", question) else 0
        ):
            question = "1. " + question

        if isBonus:
            bonuses.append(question)
        else:
            tossups.append(question)

    print(
        f"Found {len(tossups):2} tossups and {len(bonuses):2} bonuses in {bcolors.OKBLUE}{filename}{bcolors.ENDC}"
    )

    data = {
        "tossups": [],
        "bonuses": [],
    }

    skipped_tossups = 0
    for i, tossup in enumerate(tossups):
        try:
            if AUTO_INSERT_POWERMARKS and "(*)" not in tossup:
                index = tossup.rfind("{/b}")
                if index >= 0:
                    tossup = tossup[:index] + "{/b} (*) " + tossup[index:]
                else:
                    print(
                        f"{bcolors.WARNING}WARNING:{bcolors.ENDC} Could not insert powermark for tossup {i + 1} - ",
                        tossup,
                    )

            question = regex.findall(
                REGEX_TOSSUP_TEXT, remove_formatting(tossup), flags=REGEX_FLAGS
            )
            question = question[0].replace("\n", " ").strip()
            question = regex.sub(r"^\d{1,2}\.", "", question, flags=REGEX_FLAGS)
            question = question.strip()
        except:
            print(
                f"{bcolors.FAIL}ERROR:{bcolors.ENDC} cannot find question text for tossup {i + 1} - ",
                tossup,
            )
            exit(1)

        if len(question) == 0:
            print(
                f"{bcolors.FAIL}ERROR:{bcolors.ENDC} tossup {i + 1} question text is empty - ",
                tossup,
            )
            exit(1)

        try:
            answer = regex.findall(REGEX_TOSSUP_ANSWER, tossup, flags=REGEX_FLAGS)
            answer = answer[0].strip().replace("\n", " ")
            if answer.startswith(":"):
                answer = answer[1:].strip()
        except:
            print(
                f"{bcolors.FAIL}ERROR:{bcolors.ENDC} cannot find answer for tossup {i + 1} - ",
                tossup,
            )
            exit(1)

        if len(regex.findall(r"\(\*\)", question)) >= 2:
            print(
                f"{bcolors.WARNING}WARNING:{bcolors.ENDC} tossup {i + 1 + skipped_tossups} contains multiple powermarks (*)"
            )

        if "answer:" in question.lower():
            print(
                f"{bcolors.WARNING}WARNING:{bcolors.ENDC} tossup {i + 1 + skipped_tossups} question text may contain the answer"
            )
            skipped_tossups += 1

        if "answer:" in answer.lower():
            print(
                f"{bcolors.WARNING}WARNING:{bcolors.ENDC} tossup {i + 1 + skipped_tossups} answer may contain the next question"
            )
            skipped_tossups += 1
            if not HAS_QUESTION_NUMBERS:
                print(f"\n{answer}\n")

        data["tossups"].append({"question": question})

        if FORMATTED_ANSWERLINE:
            data["tossups"][i]["formatted_answer"] = format_text(answer)
            answer = remove_formatting(answer)

        data["tossups"][i]["answer"] = answer

        if HAS_CATEGORY_TAGS:
            try:
                category_tag = regex.findall(
                    REGEX_CATEGORY_TAG, remove_formatting(tossup), flags=REGEX_FLAGS
                )[0]
                category_tag = category_tag.strip().replace("\n", " ")
                subcategory = get_subcategory(category_tag)
            except:
                print(
                    f"{bcolors.FAIL}ERROR:{bcolors.ENDC} cannot find category tag for bonus {i + 1} - ",
                    bonus,
                )
                exit(3)

            if subcategory:
                category = SUBCAT_TO_CAT[subcategory]
            elif CLASSIFY_UNKNOWN_CATEGORIES:
                category, subcategory = classify_question(
                    data["tossups"][i], type="tossup"
                )
                print(
                    f"{bcolors.WARNING}WARNING:{bcolors.ENDC} tossup {i + 1} classified as {category} - {subcategory}"
                )
            else:
                print(
                    f"{bcolors.WARNING}WARNING:{bcolors.ENDC} tossup {i + 1} has unrecognized subcategory",
                    category_tag,
                )
                continue
        elif CONSTANT_CATEGORY == "" or CONSTANT_SUBCATEGORY == "":
            category, subcategory = classify_question(data["tossups"][i], type="tossup")
        else:
            category, subcategory = CONSTANT_CATEGORY, CONSTANT_SUBCATEGORY

        data["tossups"][i]["category"] = category
        data["tossups"][i]["subcategory"] = subcategory

    skipped_bonuses = 0
    for i, bonus in enumerate(bonuses):
        tags = regex.findall(REGEX_BONUS_TAGS, bonus, flags=REGEX_FLAGS)
        values = []
        for tag in tags:
            if "10" in tag:
                values.append(10)
            elif "15" in tag:
                values.append(15)
            elif "20" in tag:
                values.append(20)
            elif "5" in tag:
                values.append(5)

        difficulties = []
        for tag in tags:
            if "E" in tag or "e" in tag:
                difficulties.append("e")
            elif "M" in tag or "m" in tag:
                difficulties.append("m")
            elif "H" in tag or "h" in tag:
                difficulties.append("h")

        for typo in TEN_TYPOS:
            bonus = bonus.replace(typo, "[10]")

        try:
            leadin = regex.findall(
                REGEX_BONUS_LEADIN, remove_formatting(bonus), flags=REGEX_FLAGS
            )
            leadin = leadin[0].replace("\n", " ").strip()
            leadin = regex.sub(r"^\d{1,2}\.", "", leadin, flags=REGEX_FLAGS)
            leadin = leadin.strip()
        except:
            print(
                f"{bcolors.FAIL}ERROR:{bcolors.ENDC} cannot find leadin for bonus {i + 1} - ",
                bonus,
            )
            exit(2)

        parts = regex.findall(
            REGEX_BONUS_PARTS, remove_formatting(bonus), flags=REGEX_FLAGS
        )
        answers = regex.findall(
            REGEX_BONUS_ANSWERS, f"{bonus}\n[10]", flags=REGEX_FLAGS
        )

        if len(parts) == 0:
            print(
                f"{bcolors.FAIL}ERROR:{bcolors.ENDC} no parts found for bonus {i + 1} - ",
                bonus,
            )
            exit(2)

        if len(parts) < EXPECTED_BONUS_LENGTH:
            print(
                f"{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1} has fewer than {EXPECTED_BONUS_LENGTH} parts"
            )
            if not HAS_QUESTION_NUMBERS:
                print(f"\n{bonus[3:]}\n")

        if "answer:" in leadin.lower():
            print(
                f"{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1 + skipped_bonuses} leadin may contain the answer to the first part"
            )
            skipped_bonuses += 1
            if not HAS_QUESTION_NUMBERS:
                print(f"\n{leadin}\n")

        if len(parts) > EXPECTED_BONUS_LENGTH:
            print(
                f"{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1} has more than {EXPECTED_BONUS_LENGTH} parts"
            )

        data["bonuses"].append(
            {
                "leadin": leadin,
                "parts": [part.strip().replace("\n", " ") for part in parts],
                "values": values,
                "difficulties": difficulties,
                "answers": [],
            }
        )

        if FORMATTED_ANSWERLINE:
            data["bonuses"][i]["formatted_answers"] = []

        for answer in answers:
            answer = answer.strip().replace("\n", " ")

            if answer.startswith(":"):
                answer = answer[1:].strip()

            if FORMATTED_ANSWERLINE:
                data["bonuses"][i]["formatted_answers"].append(format_text(answer))
                answer = remove_formatting(answer)

            data["bonuses"][i]["answers"].append(answer)

        if HAS_CATEGORY_TAGS:
            try:
                category_tag = regex.findall(
                    REGEX_CATEGORY_TAG, remove_formatting(bonus), flags=REGEX_FLAGS
                )[0]
                category_tag = category_tag.strip().replace("\n", " ")
                subcategory = get_subcategory(category_tag)
            except:
                print(
                    f"{bcolors.FAIL}ERROR:{bcolors.ENDC} cannot find category tag for bonus {i + 1} - ",
                    bonus,
                )
                exit(3)

            if subcategory:
                category = SUBCAT_TO_CAT[subcategory]
            elif CLASSIFY_UNKNOWN_CATEGORIES:
                category, subcategory = classify_question(
                    data["bonuses"][i], type="bonus"
                )
                print(
                    f"{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1} classified as {category} - {subcategory}"
                )
            else:
                print(
                    f"{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1} has unrecognized subcategory",
                    category_tag,
                )
                continue
        elif CONSTANT_CATEGORY == "" or CONSTANT_SUBCATEGORY == "":
            category, subcategory = classify_question(data["bonuses"][i], type="bonus")
        else:
            category, subcategory = CONSTANT_CATEGORY, CONSTANT_SUBCATEGORY

        data["bonuses"][i]["category"] = category
        data["bonuses"][i]["subcategory"] = subcategory

    g = open(OUTPUT_DIRECTORY + filename[:-4] + ".json", "w")
    json.dump(data, g)
