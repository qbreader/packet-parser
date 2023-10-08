import click
import json
import os
import regex

from bcolors import bcolors
from classifier.classify import classify_question

# Make sure to specify both, if they are not empty strings.
# Only specifying the category will cause the program to use the question classifier.
# CONSTANT_ALTERNATE_SUBCATEGORY is optional,
# and can be used even if CONSTANT_CATEGORY or CONSTANT_SUBCATEGORY is empty.
CONSTANT_CATEGORY = ""
CONSTANT_SUBCATEGORY = ""
CONSTANT_ALTERNATE_SUBCATEGORY = ""

with open("modules/answer-typos.json") as f:
    ANSWER_TYPOS = json.load(f)

with open("modules/ten-typos.json") as f:
    TEN_TYPOS = json.load(f)

with open("modules/standardize-subcats.json") as f:
    STANDARDIZE_SUBCATS = json.load(f)

with open("modules/standardize-alternate-subcats.json") as f:
    STANDARDIZE_ALTERNATE_SUBCATS = json.load(f)

with open("modules/subcat-to-cat.json") as f:
    SUBCAT_TO_CAT = json.load(f)


def format_text(text, modaq=False):
    text = (
        text.replace("{bu}", "<b><u>")
        .replace("{/bu}", "</u></b>")
        .replace("{b}", "<b>")
        .replace("{/b}", "</b>")
        .replace("{u}", "<u>")
        .replace("{/u}", "</u>")
    )

    if modaq:
        text = text.replace("{i}", "<em>").replace("{/i}", "</em>")
    else:
        text = text.replace("{i}", "<i>").replace("{/i}", "</i>")

    return text

def get_subcategory(text: str) -> str:
    if text[0] == "<" and text[-1] == ">":
        text = text[1:-1]

    text = text.lower()
    text = text.replace("–", " ")
    text = text.replace("-", " ")
    text_split = regex.split(r"[\/, ]", text)

    for subcat in STANDARDIZE_SUBCATS:
        works = True
        for word in subcat.lower().split(" "):
            if word not in text_split:
                works = False
                break

        if works:
            return STANDARDIZE_SUBCATS[subcat]

    return ""


def get_alternate_subcategory(text: str) -> str:
    if text[0] == "<" and text[-1] == ">":
        text = text[1:-1]

    text = text.lower()
    text = text.replace("–", " ")
    text = text.replace("-", " ")
    text_split = regex.split(r"[\/, ]", text)

    for subcat in STANDARDIZE_ALTERNATE_SUBCATS:
        works = True
        for word in subcat.lower().split(" "):
            if word not in text_split:
                works = False
                break

        if works:
            return subcat

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


@click.command()
@click.option(
    "-i",
    "--input-directory",
    default="packets/",
    show_default=True,
    type=click.Path(exists=True),
)
@click.option(
    "-o", "--output-directory", default="output/", show_default=True, type=str
)
@click.option("-e", "-l", "--bonus-length", default=3, show_default=True, type=int)
@click.option(
    "-f",
    "--formatted-answerline",
    is_flag=True,
    help="Include formatted answerline in output",
)
@click.option(
    "-m",
    "--modaq",
    is_flag=True,
    help="Output in a format compatible with MODAQ.",
)
@click.option(
    "-p",
    "--auto-insert-powermarks",
    is_flag=True,
    help="Insert powermarks for questions that are bolded in power but do not have an explicit powermark.",
)
@click.option(
    "-u",
    "--classify-unknown",
    is_flag=True,
    default=True,
    show_default=True,
    help="Auto classify unrecognized categories in tags.",
)
def main(
    input_directory,
    output_directory,
    bonus_length,
    formatted_answerline,
    modaq,
    auto_insert_powermarks,
    classify_unknown,
):
    ########## START OF PROMPTS ##########

    HAS_QUESTION_NUMBERS = input("Do you have question numbers? (y/n) ") == "y"
    HAS_CATEGORY_TAGS = input("Do you have category tags? (y/n) ") == "y"
    print("Using category tags" if HAS_CATEGORY_TAGS else "Using question classifier")

    try:
        os.mkdir(output_directory)
    except FileExistsError:
        print(
            f"{bcolors.WARNING}WARNING:{bcolors.ENDC} Output directory already exists"
        )
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
    REGEX_BONUS_ANSWERS = (
        r"(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*?(?=\[(?:10)?[EMH]?\]|<[^>]*>)"
    )
    REGEX_BONUS_TAGS = r"(?<=\[)\d{0,2}?[EMH]?(?=\])"

    ########## END OF REGEX ##########

    for filename in sorted(os.listdir(input_directory)):
        if filename == ".DS_Store":
            continue

        f = open(os.path.join(input_directory, filename))
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

        for typo in ANSWER_TYPOS:
            packet_text = packet_text.replace(typo, "ANSWER:")
            packet_text = packet_text.replace(typo.title(), "ANSWER:")

        # remove redundant tags
        packet_text = regex.sub(
            r"{(bu|b|u|i)}{/\g<1>}", "", packet_text, flags=REGEX_FLAGS
        )
        packet_text = regex.sub(
            r"{/(bu|b|u|i)}{\g<1>}", "", packet_text, flags=REGEX_FLAGS
        )

        # handle html formatting at start of string
        packet_text = regex.sub(
            r"^\{(bu|b|u|i)\}(\d{1,2}|TB|X)\.",
            "1. {\g<1>}",
            packet_text,
            flags=REGEX_FLAGS,
        )
        packet_text = regex.sub(
            r"^\{(bu|b|u|i)\}ANSWER(:?)",
            "ANSWER\g<2>{\g<1>}",
            packet_text,
            flags=REGEX_FLAGS,
        )

        # handle nonstandard question numbering
        packet_text = regex.sub(
            r"^\(?(\d{1,2}|TB)\)(?=[ {])", "1. ", packet_text, flags=REGEX_FLAGS
        )
        packet_text = regex.sub(
            r"^(TB|X|Tiebreaker|Extra)[\.:]?", "21.", packet_text, flags=REGEX_FLAGS
        )
        packet_text = regex.sub(
            r"^(T|S|TU)\d{1,2}[\.:]?", "21.", packet_text, flags=REGEX_FLAGS
        )

        # handle nonstandard bonus part numbering
        packet_text = regex.sub(
            r"^[ABC][.:] *", "[10] ", packet_text, flags=REGEX_FLAGS
        )

        packet_text = regex.sub(
            r"^BS\d{1,2}[\.:]?", "21.", packet_text, flags=REGEX_FLAGS
        )

        # clear lines that are all spaces
        packet_text = regex.sub(r"^\s*$", "", packet_text, flags=REGEX_FLAGS)

        if not HAS_CATEGORY_TAGS:
            packet_text = regex.sub(REGEX_CATEGORY_TAG, "", packet_text)

        packet_questions = regex.findall(REGEX_QUESTION, packet_text, flags=REGEX_FLAGS)

        tossups = []
        bonuses = []

        for question in packet_questions:
            isBonus = regex.findall(
                r"^\[(5|10|15)?[EMH]?\]", question, flags=REGEX_FLAGS
            )

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
                if auto_insert_powermarks and "(*)" not in tossup:
                    index = tossup.rfind("{/b}")
                    if index >= 0:
                        tossup = tossup[:index] + "{/b} (*) " + tossup[index:]
                    else:
                        print(
                            f"{bcolors.WARNING}WARNING:{bcolors.ENDC} Could not insert powermark for tossup {i + 1} - ",
                            tossup,
                        )

                question = regex.findall(REGEX_TOSSUP_TEXT, tossup, flags=REGEX_FLAGS)
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

            if modaq:
                question = format_text(question, True)
            else:
                question = remove_formatting(question)

            data["tossups"].append({ "question": question })

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

            if modaq:
                data["tossups"][i]["answer"] = format_text(answer, True)
            elif formatted_answerline:
                data["tossups"][i]["formatted_answer"] = format_text(answer)
                data["tossups"][i]["answer"] = remove_formatting(answer)
            else:
                data["tossups"][i]["answer"] = remove_formatting(answer)

            if HAS_CATEGORY_TAGS:
                try:
                    category_tag = regex.findall(
                        REGEX_CATEGORY_TAG, remove_formatting(tossup), flags=REGEX_FLAGS
                    )[0]
                    category_tag = category_tag.strip().replace("\n", " ")
                    subcategory = get_subcategory(category_tag)
                    alternate_subcategory = get_alternate_subcategory(category_tag)
                    if alternate_subcategory:
                        data["tossups"][i][
                            "alternate_subcategory"
                        ] = alternate_subcategory
                except:
                    print(
                        f"{bcolors.FAIL}ERROR:{bcolors.ENDC} cannot find category tag for tossup {i + 1} - ",
                        tossup,
                    )
                    exit(3)

                if modaq:
                    data['tossups'][i]['metadata'] = category_tag[1:-1]

                if subcategory:
                    category = SUBCAT_TO_CAT[subcategory]
                elif classify_unknown:
                    category, subcategory = classify_question(
                        data["tossups"][i], type="tossup"
                    )
                    if not alternate_subcategory:
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
                category, subcategory = classify_question(
                    data["tossups"][i], type="tossup"
                )
            else:
                category, subcategory = CONSTANT_CATEGORY, CONSTANT_SUBCATEGORY

            if CONSTANT_ALTERNATE_SUBCATEGORY:
                data["tossups"][i][
                    "alternate_subcategory"
                ] = CONSTANT_ALTERNATE_SUBCATEGORY

            if not modaq:
                data["tossups"][i]["category"] = category
                data["tossups"][i]["subcategory"] = subcategory

            if modaq and not data['tossups'][i]['metadata']:
                data['tossups'][i]['metadata'] = category_tag[1:-1]

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
                leadin = regex.findall(REGEX_BONUS_LEADIN, bonus, flags=REGEX_FLAGS)
                leadin = leadin[0].replace("\n", " ").strip()
                leadin = regex.sub(r"^\d{1,2}\.", "", leadin, flags=REGEX_FLAGS)
                leadin = leadin.strip()
            except:
                print(
                    f"{bcolors.FAIL}ERROR:{bcolors.ENDC} cannot find leadin for bonus {i + 1} - ",
                    bonus,
                )
                exit(2)

            if modaq:
                data["bonuses"].append({
                    "leadin": format_text(leadin, True),
                    "leadin_sanitized": remove_formatting(leadin),
                })
            else:
                data["bonuses"].append({
                    "leadin": remove_formatting(leadin)
                })

            parts = regex.findall(REGEX_BONUS_PARTS, bonus, flags=REGEX_FLAGS)
            parts = [part.strip().replace("\n", " ") for part in parts]

            if len(parts) == 0:
                print(
                    f"{bcolors.FAIL}ERROR:{bcolors.ENDC} no parts found for bonus {i + 1} - ",
                    bonus,
                )
                exit(2)

            if len(parts) < bonus_length:
                print(
                    f"{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1} has fewer than {bonus_length} parts"
                )
                if not HAS_QUESTION_NUMBERS:
                    print(f"\n{bonus[3:]}\n")

            if len(parts) > bonus_length:
                print(
                    f"{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1} has more than {bonus_length} parts"
                )

            if modaq:
                data['bonuses'][i]["parts"] = [format_text(part, True) for part in parts]
                data['bonuses'][i]["parts_sanitized"] = [remove_formatting(part) for part in parts]
            else:
                data['bonuses'][i]["parts"] = [remove_formatting(part) for part in parts]

            answers = regex.findall(REGEX_BONUS_ANSWERS, f"{bonus}\n[10]", flags=REGEX_FLAGS)

            if "answer:" in leadin.lower():
                print(
                    f"{bcolors.WARNING}WARNING:{bcolors.ENDC} bonus {i + 1 + skipped_bonuses} leadin may contain the answer to the first part"
                )
                skipped_bonuses += 1
                if not HAS_QUESTION_NUMBERS:
                    print(f"\n{leadin}\n")

            for j, answer in enumerate(answers):
                answer = answer.strip().replace("\n", " ")

                if answer.startswith(":"):
                    answer = answer[1:].strip()

                answers[j] = answer

            if modaq:
                data["bonuses"][i]["answers"] = [format_text(answer, True) for answer in answers]
                data["bonuses"][i]["answers_sanitized"] = [remove_formatting(answer) for answer in answers]
            elif formatted_answerline:
                data["bonuses"][i]["formatted_answers"] = [format_text(answer) for answer in answers]
                data["bonuses"][i]["answers"] = [remove_formatting(answer) for answer in answers]
            else:
                data["bonuses"][i]["answers"] = [remove_formatting(answer) for answer in answers]

            if len(values) > 0:
                data["bonuses"][i]["values"] = values
            elif modaq:
                data["bonuses"][i]["values"] = [10 for _ in range(len(parts))]

            if len(difficulties) > 0:
                if modaq:
                    data["bonuses"][i]["difficultyModifiers"] = difficulties
                else:
                    data["bonuses"][i]["difficulties"] = difficulties

            if HAS_CATEGORY_TAGS:
                try:
                    category_tag = regex.findall(
                        REGEX_CATEGORY_TAG, remove_formatting(bonus), flags=REGEX_FLAGS
                    )[0]
                    category_tag = category_tag.strip().replace("\n", " ")
                    subcategory = get_subcategory(category_tag)
                    alternate_subcategory = get_alternate_subcategory(category_tag)
                    if alternate_subcategory:
                        data["bonuses"][i][
                            "alternate_subcategory"
                        ] = alternate_subcategory
                except:
                    print(
                        f"{bcolors.FAIL}ERROR:{bcolors.ENDC} cannot find category tag for bonus {i + 1} - ",
                        bonus,
                    )
                    exit(3)

                if modaq:
                    data['bonuses'][i]['metadata'] = category_tag[1:-1]

                if subcategory:
                    category = SUBCAT_TO_CAT[subcategory]
                elif classify_unknown:
                    category, subcategory = classify_question(
                        data["bonuses"][i], type="bonus"
                    )
                    if not alternate_subcategory:
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
                category, subcategory = classify_question(
                    data["bonuses"][i], type="bonus"
                )
            else:
                category, subcategory = CONSTANT_CATEGORY, CONSTANT_SUBCATEGORY

            if CONSTANT_ALTERNATE_SUBCATEGORY:
                data["bonuses"][i][
                    "alternate_subcategory"
                ] = CONSTANT_ALTERNATE_SUBCATEGORY

            if not modaq:
                data["bonuses"][i]["category"] = category
                data["bonuses"][i]["subcategory"] = subcategory

            if modaq and not data['bonuses'][i]['metadata']:
                data['bonuses'][i]['metadata'] = category + " - " + subcategory

        g = open(output_directory + filename[:-4] + ".json", "w")
        json.dump(data, g)


if __name__ == "__main__":
    main()
