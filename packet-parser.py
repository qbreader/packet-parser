import click
import json
import os
import regex

from bcolors import bcolors
from classifier.classify import classify_question

CONSTANT_SUBCATEGORY = ""
# CONSTANT_ALTERNATE_SUBCATEGORY is optional,
# and can be used even if CONSTANT_SUBCATEGORY is empty.
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


def format_text(text: str, modaq=False) -> str:
    text = (
        text.replace("{b}", "<b>")
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
    text_split = regex.split(r"[\/,; ]", text)

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
    text_split = regex.split(r"[\/,; ]", text)

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
        text.replace("{b}", "")
        .replace("{/b}", "")
        .replace("{u}", "")
        .replace("{/u}", "")
    )

    if not include_italics:
        text = text.replace("{i}", "").replace("{/i}", "")

    return text


def remove_punctuation(s: str, punctuation=""".,!-;:'"\/?@#$%^&*_~()[]{}“”‘’"""):
    return "".join(ch for ch in s if ch not in punctuation)


class Parser:
    REGEX_FLAGS = regex.IGNORECASE | regex.MULTILINE

    def __init__(
        self,
        has_question_numbers: bool,
        has_category_tags: bool,
        bonus_length: int,
        formatted_answerline: bool,
        modaq: bool,
        auto_insert_powermarks: bool,
        classify_unknown: bool,
        constant_subcategory: str = "",
        constant_alternate_subcategory: str = "",
    ) -> None:
        self.has_question_numbers = has_question_numbers
        self.has_category_tags = has_category_tags

        self.bonus_length = bonus_length
        self.formatted_answerline = formatted_answerline
        self.modaq = modaq
        self.auto_insert_powermarks = auto_insert_powermarks
        self.classify_unknown = classify_unknown

        self.tossup_index: int = 0
        """
        1-indexed
        """
        self.bonus_index: int = 0
        """
        1-indexed
        """

        self.constant_subcategory = constant_subcategory
        self.constant_category = (
            SUBCAT_TO_CAT[constant_subcategory] if constant_subcategory else ""
        )
        self.constant_alternate_subcategory = constant_alternate_subcategory

        if not self.has_category_tags and not self.constant_subcategory == "":
            Parser.print_warning(
                f"Using fixed category {self.constant_category} and subcategory {self.constant_subcategory}"
            )

        if self.constant_alternate_subcategory:
            Parser.print_warning(
                f"Using fixed alternate subcategory {self.constant_alternate_subcategory}"
            )

        self.__init_regex__()

    def __init_regex__(self):
        if self.has_question_numbers and self.has_category_tags:
            self.REGEX_QUESTION = r"^ *\d{1,2}\.(?:.|\n)*?ANSWER(?:.|\n)*?<[^>]*>"
        elif self.has_question_numbers:
            # self.REGEX_QUESTION = r"^ *\d{1,2}\.(?:.|\n)*?ANSWER(?:.*\n)*?(?= *\d{1,2}\.)"
            self.REGEX_QUESTION = r"\d{0,2}(?:[^\d\n].*\n)*[ \t]*ANSWER.*(?:\n.+)*?(?=\n\s*\d{1,2}|\n\s*$)"
        else:
            self.REGEX_QUESTION = r"(?:[^\n].*\n)*[ \t]*ANSWER.*(?:\n.*)*?(?=\n$)"

        self.REGEX_CATEGORY_TAG = r"<[^>]*>"

        self.REGEX_TOSSUP_TEXT = r"(?<=\d{1,2}\.)(?:.|\n)*?(?=^ ?ANSWER|ANSWER:)"
        self.REGEX_TOSSUP_ANSWER = (
            r"(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*(?=<[^>]*>)"
            if self.has_category_tags
            else r"(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*"
        )

        self.REGEX_BONUS_LEADIN = r"(?<=^ *\d{1,2}\.)(?:.|\n)*?(?=\[(?:10)?[EMH]?\])"
        self.REGEX_BONUS_PARTS = (
            r"(?<=\[(?:10)?[EMH]?\])(?:.|\n)*?(?=^ ?ANSWER|ANSWER:)"
        )
        self.REGEX_BONUS_ANSWERS = (
            r"(?<=ANSWER:|^ ?ANSWER)(?:.|\n)*?(?=\[(?:10)?[EMH]?\]|<[^>]*>)"
        )
        self.REGEX_BONUS_TAGS = r"(?<=\[)\d{0,2}?[EMH]?(?=\])"

    @staticmethod
    def print_error(message: str):
        print(f"{bcolors.FAIL}ERROR:{bcolors.ENDC} {message}")

    @staticmethod
    def print_warning(message: str):
        print(f"{bcolors.WARNING}WARNING:{bcolors.ENDC} {message}")

    def parse_tossup(self, text: str) -> dict:
        data = {}

        if self.auto_insert_powermarks and "(*)" not in text:
            index = text.rfind("{/b}")
            if index >= 0:
                text = text[:index] + "{/b} (*) " + text[index:]
            else:
                Parser.print_warning(
                    f"Could not insert powermark for tossup {self.tossup_index} - {text}"
                )

        try:
            question: str = regex.findall(
                self.REGEX_TOSSUP_TEXT, text, flags=Parser.REGEX_FLAGS
            )[0]
            question = question.replace("\n", " ").strip()
            question = regex.sub(r"^\d{1,2}\.", "", question, flags=Parser.REGEX_FLAGS)
            question = question.strip()
        except:
            Parser.print_error(
                f"Cannot find question text for tossup {self.tossup_index} - {text}"
            )
            exit(1)

        if len(question) == 0:
            Parser.print_error(
                f"Tossup {self.tossup_index} question text is empty - {text}"
            )
            exit(1)

        if len(regex.findall(r"\(\*\)", question)) >= 2:
            Parser.print_warning(
                f"Tossup {self.tossup_index} contains multiple powermarks (*)"
            )

        unformatted_question = remove_formatting(question)
        if "(*)" in question and " (*) " not in unformatted_question:
            Parser.print_warning(
                f"Tossup {self.tossup_index} powermark (*) is not surrounded by spaces"
            )

        if self.modaq:
            question = format_text(question, True)
        else:
            question = unformatted_question

        data["question"] = question

        try:
            answer: list[str] = regex.findall(
                self.REGEX_TOSSUP_ANSWER, text, flags=Parser.REGEX_FLAGS
            )
            answer = answer[0].strip().replace("\n", " ")
            if answer.startswith(":"):
                answer = answer[1:].strip()
        except:
            Parser.print_error(
                f"Cannot find answer for tossup {self.tossup_index + 1} - {text}"
            )
            exit(1)

        if "answer:" in question.lower():
            Parser.print_warning(
                f"Tossup {self.tossup_index} question text may contain the answer"
            )
            self.tossup_index += 1

        if "answer:" in answer.lower():
            Parser.print_warning(
                f"Tossup {self.tossup_index} answer may contain the next question"
            )
            self.tossup_index += 1
            if not self.has_category_tags:
                print(f"\n{answer}\n")

        if self.modaq:
            data["answer"] = format_text(answer, True)
        elif self.formatted_answerline:
            data["formatted_answer"] = format_text(answer)
            data["answer"] = remove_formatting(answer)
        else:
            data["answer"] = remove_formatting(answer)

        if self.has_category_tags:
            try:
                category_tag: list[str] = regex.findall(
                    self.REGEX_CATEGORY_TAG,
                    remove_formatting(text),
                    flags=Parser.REGEX_FLAGS,
                )
                category_tag = category_tag[0].strip().replace("\n", " ")
                subcategory = get_subcategory(category_tag)
                alternate_subcategory = get_alternate_subcategory(category_tag)
                if alternate_subcategory:
                    data["alternate_subcategory"] = alternate_subcategory
            except:
                Parser.print_error(
                    f"Cannot find category tag for tossup {self.tossup_index} - {text}"
                )
                exit(3)

            if self.modaq:
                data["metadata"] = category_tag[1:-1]

            if subcategory:
                category = SUBCAT_TO_CAT[subcategory]
            elif self.classify_unknown:
                category, subcategory = classify_question(data, type="tossup")
                if not alternate_subcategory:
                    Parser.print_warning(
                        f"Tossup {self.tossup_index} classified as {category} / {subcategory}"
                    )
            else:
                Parser.print_warning(
                    f"Tossup {self.tossup_index} has unrecognized subcategory {category_tag}"
                )
        elif self.constant_category == "" or self.constant_subcategory == "":
            category, subcategory = classify_question(data, type="tossup")
        else:
            category = self.constant_category
            subcategory = self.constant_subcategory

        if self.constant_alternate_subcategory:
            data["alternate_subcategory"] = self.constant_alternate_subcategory

        if not self.modaq:
            data["category"] = category
            data["subcategory"] = subcategory

        if self.modaq and not data["metadata"]:
            data["metadata"] = category + " - " + subcategory

        return data

    def parse_bonus(self, text: str) -> dict:
        data = {}

        tags = regex.findall(self.REGEX_BONUS_TAGS, text, flags=Parser.REGEX_FLAGS)
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

        if len(values) > 0:
            data["values"] = values
        elif self.modaq:
            data["values"] = [10 for _ in range(len(parts))]

        if len(difficulties) > 0:
            if self.modaq:
                data["difficultyModifiers"] = difficulties
            else:
                data["difficulties"] = difficulties

        for typo in TEN_TYPOS:
            text = text.replace(typo, "[10]")

        try:
            leadin = regex.findall(
                self.REGEX_BONUS_LEADIN, text, flags=Parser.REGEX_FLAGS
            )
            leadin = leadin[0].replace("\n", " ").strip()
            leadin = regex.sub(r"^\d{1,2}\.", "", leadin, flags=Parser.REGEX_FLAGS)
            leadin = leadin.strip()
        except:
            Parser.print_error(
                f"Cannot find leadin for bonus {self.bonus_index} - {text}"
            )
            exit(2)

        if self.modaq:
            data["leadin"] = format_text(leadin, True)
            data["leadin_sanitized"] = remove_formatting(leadin)
        else:
            data["leadin"] = remove_formatting(leadin)

        parts: list[str] = regex.findall(
            self.REGEX_BONUS_PARTS, text, flags=Parser.REGEX_FLAGS
        )
        parts = [part.strip().replace("\n", " ") for part in parts]

        if len(parts) == 0:
            Parser.print_error(f"No parts found for bonus {self.bonus_index} - {text}")
            exit(2)

        if len(parts) < self.bonus_length:
            Parser.print_warning(
                f"Bonus {self.bonus_index} has fewer than {self.bonus_length} parts"
            )
            if not self.has_question_numbers:
                print(f"\n{text[3:]}\n")

        if len(parts) > self.bonus_length:
            Parser.print_warning(
                f"Bonus {self.bonus_index} has more than {self.bonus_length} parts"
            )

        if self.modaq:
            data["parts"] = [format_text(part, True) for part in parts]
            data["parts_sanitized"] = [remove_formatting(part) for part in parts]
        else:
            data["parts"] = [remove_formatting(part) for part in parts]

        answers: list[str] = regex.findall(
            self.REGEX_BONUS_ANSWERS, f"{text}\n[10]", flags=Parser.REGEX_FLAGS
        )

        if "answer:" in leadin.lower():
            Parser.print_warning(
                f"Bonus {self.bonus_index} leadin may contain the answer to the first part"
            )
            self.bonus_index += 1
            if not self.has_question_numbers:
                print(f"\n{leadin}\n")

        for j, answer in enumerate(answers):
            answer = answer.strip().replace("\n", " ")

            if answer.startswith(":"):
                answer = answer[1:].strip()

            answers[j] = answer

        if self.modaq:
            data["answers"] = [format_text(answer, True) for answer in answers]
            data["answers_sanitized"] = [
                remove_formatting(answer) for answer in answers
            ]
        elif self.formatted_answerline:
            data["formatted_answers"] = [format_text(answer) for answer in answers]
            data["answers"] = [remove_formatting(answer) for answer in answers]
        else:
            data["answers"] = [remove_formatting(answer) for answer in answers]

        if self.has_category_tags:
            try:
                category_tag = regex.findall(
                    self.REGEX_CATEGORY_TAG,
                    remove_formatting(text),
                    flags=Parser.REGEX_FLAGS,
                )[0]
                category_tag = category_tag.strip().replace("\n", " ")
                subcategory = get_subcategory(category_tag)
                alternate_subcategory = get_alternate_subcategory(category_tag)
                if alternate_subcategory:
                    data["alternate_subcategory"] = alternate_subcategory
            except:
                Parser.print_error(
                    f"Cannot find category tag for bonus {self.bonus_index} - {text}"
                )
                exit(3)

            if self.modaq:
                data["metadata"] = category_tag[1:-1]

            if subcategory:
                category = SUBCAT_TO_CAT[subcategory]
            elif self.classify_unknown:
                category, subcategory = classify_question(data, type="bonus")
                if not alternate_subcategory:
                    Parser.print_warning(
                        f"Bonus {self.bonus_index} classified as {category} - {subcategory}"
                    )
            else:
                Parser.print_warning(
                    f"Bonus {self.bonus_index} has unrecognized subcategory {category_tag}"
                )
        elif self.constant_category == "" or self.constant_subcategory == "":
            category, subcategory = classify_question(data, type="bonus")
        else:
            category, subcategory = self.constant_category, self.constant_subcategory

        if self.constant_alternate_subcategory:
            data["alternate_subcategory"] = self.constant_alternate_subcategory

        if not self.modaq:
            data["category"] = category
            data["subcategory"] = subcategory

        if self.modaq and not data["metadata"]:
            data["metadata"] = category + " - " + subcategory

        return data

    def preprocess_packet(self, packet_text: str) -> str:
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
            r"{(bu|b|u|i)}{/\g<1>}", "", packet_text, flags=Parser.REGEX_FLAGS
        )
        packet_text = regex.sub(
            r"{/(bu|b|u|i)}{\g<1>}", "", packet_text, flags=Parser.REGEX_FLAGS
        )

        # handle html formatting at start of string
        packet_text = regex.sub(
            r"^\{(bu|b|u|i)\}(\d{1,2}|TB|X)\.",
            "1. {\g<1>}",
            packet_text,
            flags=Parser.REGEX_FLAGS,
        )
        packet_text = regex.sub(
            r"^\{(bu|b|u|i)\}ANSWER(:?)",
            "ANSWER\g<2>{\g<1>}",
            packet_text,
            flags=Parser.REGEX_FLAGS,
        )

        # handle nonstandard question numbering
        packet_text = regex.sub(
            r"^\(?(\d{1,2}|TB)\)(?=[ {])", "1. ", packet_text, flags=Parser.REGEX_FLAGS
        )
        packet_text = regex.sub(
            r"^(TB|X|Tiebreaker|Extra)[\.:]?",
            "21.",
            packet_text,
            flags=Parser.REGEX_FLAGS,
        )
        packet_text = regex.sub(
            r"^(T|S|TU)\d{1,2}[\.:]?", "21.", packet_text, flags=Parser.REGEX_FLAGS
        )

        # handle nonstandard bonus part numbering
        packet_text = regex.sub(
            r"^[ABC][.:] *", "[10] ", packet_text, flags=Parser.REGEX_FLAGS
        )

        packet_text = regex.sub(
            r"^BS\d{1,2}[\.:]?", "21.", packet_text, flags=Parser.REGEX_FLAGS
        )

        # clear lines that are all spaces
        packet_text = regex.sub(r"^\s*$", "", packet_text, flags=Parser.REGEX_FLAGS)

        if not self.has_category_tags:
            packet_text = regex.sub(self.REGEX_CATEGORY_TAG, "", packet_text)

        return packet_text

    def parse_packet(self, packet_text: str, packet_name="") -> dict:
        self.tossup_index = 1
        self.bonus_index = 1

        packet_text = self.preprocess_packet(packet_text)

        packet_questions = regex.findall(
            self.REGEX_QUESTION, packet_text, flags=Parser.REGEX_FLAGS
        )

        tossups = []
        bonuses = []

        for question in packet_questions:
            isBonus = regex.findall(
                r"^\[(5|10|15)?[EMH]?\]", question, flags=Parser.REGEX_FLAGS
            )

            if (not self.has_question_numbers) ^ (
                1 if regex.match("^\d{1,2}\.", question) else 0
            ):
                question = "1. " + question

            if isBonus:
                bonuses.append(question)
            else:
                tossups.append(question)

        if packet_name:
            print(
                f"Found {len(tossups):2} tossups and {len(bonuses):2} bonuses in {bcolors.OKBLUE}{packet_name}{bcolors.ENDC}"
            )

        data = {
            "tossups": [],
            "bonuses": [],
        }

        for tossup in tossups:
            data["tossups"].append(self.parse_tossup(tossup))
            self.tossup_index += 1

        for bonus in bonuses:
            data["bonuses"].append(self.parse_bonus(bonus))
            self.bonus_index += 1

        return data


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

    parser = Parser(
        HAS_QUESTION_NUMBERS,
        HAS_CATEGORY_TAGS,
        bonus_length,
        formatted_answerline,
        modaq,
        auto_insert_powermarks,
        classify_unknown,
        CONSTANT_SUBCATEGORY,
        CONSTANT_ALTERNATE_SUBCATEGORY,
    )

    for filename in sorted(os.listdir(input_directory)):
        if filename == ".DS_Store":
            continue

        f = open(os.path.join(input_directory, filename))

        packet_text = ""
        for line in f.readlines():
            packet_text += line

        packet = parser.parse_packet(packet_text, filename)

        g = open(output_directory + filename[:-4] + ".json", "w")
        json.dump(packet, g)


if __name__ == "__main__":
    main()
