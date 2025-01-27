from typing import Literal

import click
import json
import os
import regex

from bcolors import bcolors
from classifier.classify import (
    classify,
    classify_question,
    ALTERNATE_SUBCATEGORIES,
    SUBSUBCATEGORIES,
)

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

    return text.strip()


def get_subcategory(text: str) -> str:
    if text[0] == "<" and text[-1] == ">":
        text = text[1:-1]

    text = text.lower()
    text = text.replace("–", " ")
    text = text.replace("—", " ")
    text = text.replace("-", " ")
    text_split = regex.split(r"[\/,;:. ]", text)

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
            return STANDARDIZE_ALTERNATE_SUBCATS[subcat]

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

    return text.strip()


def remove_punctuation(s: str, punctuation=""".,!-;:'"\/?@#$%^&*_~()[]{}“”‘’"""):
    return "".join(ch for ch in s if ch not in punctuation)


class Logger:
    @staticmethod
    def error(message: str):
        print(f"{bcolors.FAIL}ERROR:{bcolors.ENDC} {message}")

    @staticmethod
    def warning(message: str):
        print(f"{bcolors.WARNING}WARNING:{bcolors.ENDC} {message}")


class Parser:
    REGEX_FLAGS = regex.IGNORECASE | regex.MULTILINE

    def __init__(
        self,
        has_question_numbers: bool,
        has_category_tags: bool,
        bonus_length: int,
        buzzpoints: bool,
        modaq: bool,
        auto_insert_powermarks: bool,
        classify_unknown: bool,
        space_powermarks: bool,
        always_classify: bool = False,
        constant_subcategory: str = "",
        constant_alternate_subcategory: str = "",
    ) -> None:
        self.has_question_numbers = has_question_numbers
        self.has_category_tags = has_category_tags

        self.bonus_length = bonus_length
        self.buzzpoints = buzzpoints
        self.modaq = modaq
        self.auto_insert_powermarks = auto_insert_powermarks
        self.classify_unknown = classify_unknown
        self.space_powermarks = space_powermarks
        self.always_classify = always_classify

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
            Logger.warning(
                f"Using fixed category {self.constant_category} and subcategory {self.constant_subcategory}"
            )

        if self.constant_alternate_subcategory:
            Logger.warning(
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

    def parse_tossup(self, text: str) -> dict:
        category, subcategory, alternate_subcategory, metadata = self.parse_category(
            text, "tossup"
        )

        if not self.has_category_tags:
            text = regex.sub(self.REGEX_CATEGORY_TAG, "", text)

        question_raw = regex.search(
            self.REGEX_TOSSUP_TEXT, text, flags=Parser.REGEX_FLAGS
        )
        if not question_raw:
            Logger.error(f"No question text for tossup {self.tossup_index} - {text}")
            exit(1)

        question_raw = question_raw.group()
        question_raw = question_raw.replace("\n", " ").strip()
        question_raw = regex.sub(
            r"^\d{1,2}\.", "", question_raw, flags=Parser.REGEX_FLAGS
        )
        question_raw = question_raw.strip()

        if len(question_raw) == 0:
            Logger.error(f"Tossup {self.tossup_index} question text is empty - {text}")
            exit(1)

        if len(regex.findall(r"\(\*\)", question_raw)) >= 2:
            Logger.warning(f"Tossup {self.tossup_index} has multiple powermarks (*)")

        if self.auto_insert_powermarks and "(*)" not in question_raw:
            question_raw = self.insert_powermark(question_raw)

        if question_raw.startswith("{b}{i} "):
            question_raw = "{b}{i}" + question_raw[6:]
        elif question_raw.startswith("{b} "):
            question_raw = "{b}" + question_raw[4:]
        elif question_raw.startswith("{i} "):
            question_raw = "{i}" + question_raw[4:]

        question = format_text(question_raw, self.modaq)
        question_sanitized = remove_formatting(question_raw)

        if "(*)" in question_sanitized and " (*) " not in question_sanitized:
            if self.space_powermarks:
                question_sanitized = regex.sub(
                    r" *\(\*\) *", " (*) ", question_sanitized
                )
                question = regex.sub(r" *\(\*\) *", " (*) ", question)
            else:
                Logger.warning(
                    f"Tossup {self.tossup_index} powermark (*) is not surrounded by spaces"
                )

        if "answer:" in question_sanitized.lower():
            Logger.warning(
                f"Tossup {self.tossup_index} question text may contain the answer"
            )
            self.tossup_index += 1

        answer_raw = regex.search(
            self.REGEX_TOSSUP_ANSWER, text, flags=Parser.REGEX_FLAGS
        )

        if not answer_raw:
            Logger.error(f"Cannot find answer for tossup {self.tossup_index} - {text}")
            exit(1)

        answer_raw = answer_raw.group()
        answer_raw = answer_raw.replace("\n", " ").strip()
        if answer_raw.startswith(":"):
            answer_raw = answer_raw[1:].strip()

        if "answer:" in answer_raw.lower():
            Logger.warning(
                f"Tossup {self.tossup_index} answer may contain the next question"
            )
            self.tossup_index += 1
            if not self.has_category_tags:
                print(f"\n{answer_raw}\n")

        answer = format_text(answer_raw, self.modaq)
        answer_sanitized = remove_formatting(answer_raw)

        if self.buzzpoints:
            data = {
                "question": question,
                "answer": answer,
                "answer_sanitized": answer_sanitized,
                "metadata": metadata,
            }

            return data
        elif self.modaq:
            data = {
                "question": question,
                "answer": answer,
                "metadata": metadata,
            }

            return data
        else:
            data = {
                "question": question,
                "question_sanitized": question_sanitized,
                "answer": answer,
                "answer_sanitized": answer_sanitized,
                "category": category,
                "subcategory": subcategory,
                "alternate_subcategory": alternate_subcategory,
            }

            if alternate_subcategory == "":
                del data["alternate_subcategory"]

        return data

    def parse_bonus(self, text: str) -> dict:
        category, subcategory, alternate_subcategory, metadata = self.parse_category(
            text, "bonus"
        )

        if not self.has_category_tags:
            text = regex.sub(self.REGEX_CATEGORY_TAG, "", text)

        difficultyModifiers, values = self.parse_bonus_tags(text)

        for typo in TEN_TYPOS:
            text = text.replace(typo, "[10]")

        leadin_raw = regex.search(
            self.REGEX_BONUS_LEADIN, text, flags=Parser.REGEX_FLAGS
        )

        if not leadin_raw:
            Logger.error(f"Cannot find leadin for bonus {self.bonus_index} - {text}")
            exit(2)

        leadin_raw = leadin_raw.group()
        leadin_raw = leadin_raw.replace("\n", " ").strip()
        leadin_raw = regex.sub(r"^\d{1,2}\.", "", leadin_raw, flags=Parser.REGEX_FLAGS)
        leadin_raw = leadin_raw.strip()

        if leadin_raw.startswith("{b}{i} "):
            leadin_raw = "{b}{i}" + leadin_raw[6:]
        elif leadin_raw.startswith("{b} "):
            leadin_raw = "{b}" + leadin_raw[4:]
        elif leadin_raw.startswith("{i} "):
            leadin_raw = "{i}" + leadin_raw[4:]

        leadin = format_text(leadin_raw, self.modaq)
        leadin_sanitized = remove_formatting(leadin_raw)

        if "answer:" in leadin_sanitized.lower():
            Logger.warning(
                f"Bonus {self.bonus_index} leadin may contain the answer to the first part"
            )
            self.bonus_index += 1
            if not self.has_question_numbers:
                print(f"\n{leadin_raw}\n")

        parts_raw: list[str] = regex.findall(
            self.REGEX_BONUS_PARTS, text, flags=Parser.REGEX_FLAGS
        )

        if len(parts_raw) == 0:
            Logger.error(f"No parts found for bonus {self.bonus_index} - {text}")
            exit(2)

        parts_raw = [part.replace("\n", " ").strip() for part in parts_raw]
        parts = [format_text(part, self.modaq) for part in parts_raw]
        parts_sanitized = [remove_formatting(part) for part in parts_raw]

        answers_raw: list[str] = regex.findall(
            self.REGEX_BONUS_ANSWERS, f"{text}\n[10]", flags=Parser.REGEX_FLAGS
        )

        if len(answers_raw) == 0:
            Logger.error(f"No answers found for bonus {self.bonus_index} - {text}")
            exit(2)

        answers_raw = [answer.replace("\n", " ").strip() for answer in answers_raw]
        answers_raw = [
            answer[1:].strip() if answer.startswith(":") else answer
            for answer in answers_raw
        ]
        answers = [format_text(answer, self.modaq) for answer in answers_raw]
        answers_sanitized = [remove_formatting(answer) for answer in answers_raw]

        if len(parts_raw) != len(answers_raw):
            Logger.warning(
                f"Bonus {self.bonus_index} has {len(parts_raw)} parts but {len(answers_raw)} answers"
            )

        if len(parts_raw) < self.bonus_length and sum(values) != 30:
            Logger.warning(
                f"Bonus {self.bonus_index} has fewer than {self.bonus_length} parts"
            )
            if not self.has_question_numbers:
                print(f"\n{text[3:]}\n")

        if len(parts_raw) > self.bonus_length and sum(values) != 30:
            Logger.warning(
                f"Bonus {self.bonus_index} has more than {self.bonus_length} parts"
            )

        if "answer:" in answers_sanitized[-1].lower():
            Logger.warning(
                f"Bonus {self.bonus_index} answer may contain the next tossup"
            )
            print(f"\n{answers_sanitized[-1]}\n")

        if self.buzzpoints:
            data = {
                "values": values,
                "leadin": leadin,
                "leadin_sanitized": leadin_sanitized,
                "parts": parts,
                "parts_sanitized": parts_sanitized,
                "answers": answers,
                "answers_sanitized": answers_sanitized,
                "metadata": metadata,
                "difficultyModifiers": difficultyModifiers,
            }

            if len(difficultyModifiers) == 0:
                del data["difficultyModifiers"]

            return data

        elif self.modaq:
            data = {
                "values": values,
                "leadin": leadin,
                "parts": parts,
                "answers": answers,
                "metadata": metadata,
                "difficultyModifiers": difficultyModifiers,
            }

            if len(difficultyModifiers) == 0:
                del data["difficultyModifiers"]

            return data
        else:
            data = {
                "leadin": leadin,
                "leadin_sanitized": leadin_sanitized,
                "parts": parts,
                "parts_sanitized": parts_sanitized,
                "answers": answers,
                "answers_sanitized": answers_sanitized,
                "category": category,
                "subcategory": subcategory,
                "alternate_subcategory": alternate_subcategory,
                "values": values,
                "difficultyModifiers": difficultyModifiers,
            }

            if alternate_subcategory == "":
                del data["alternate_subcategory"]

            if len(values) == 0:
                del data["values"]

            if len(difficultyModifiers) == 0:
                del data["difficultyModifiers"]

            return data

    def insert_powermark(self, text: str) -> str:
        index = text.rfind("{/b}")
        if index < 0:
            Logger.warning(f"Can't insert (*) for tossup {self.tossup_index} - {text}")

        return text[:index] + "(*)" + text[index:]

    def parse_category(
        self, text: str, type: Literal["tossup", "bonus"]
    ) -> tuple[str, str, str, str]:
        category = ""
        subcategory = ""
        alternate_subcategory = ""
        metadata = ""

        index = self.tossup_index if type == "tossup" else self.bonus_index

        category_tag = self.parse_category_tag(text)

        if category_tag:
            category, subcategory, alternate_subcategory, metadata = category_tag
        elif self.has_category_tags:
            Logger.error(f"No category tag for {type} {index} - {text}")
            exit(3)

        if self.constant_category and self.constant_subcategory:
            category = self.constant_category
            subcategory = self.constant_subcategory

        if self.constant_alternate_subcategory:
            alternate_subcategory = self.constant_alternate_subcategory

        if not subcategory and self.has_category_tags and not self.classify_unknown:
            Logger.error(f"{type} {index} has unrecognized subcategory {category_tag}")
            exit(3)

        if not subcategory or (not self.has_category_tags and self.always_classify):
            category, subcategory, temp_alternate_subcategory = classify_question(text)

            if self.has_category_tags and not alternate_subcategory:
                Logger.warning(
                    f"{type} {index} classified as {category} - {subcategory}"
                )

            if not alternate_subcategory:
                alternate_subcategory = temp_alternate_subcategory

        if not alternate_subcategory and not self.modaq:
            if category in ALTERNATE_SUBCATEGORIES:
                alternate_subcategory = classify(
                    text,
                    mode="alternate-subcategory",
                    category=category,
                )
            elif subcategory in SUBSUBCATEGORIES:
                alternate_subcategory = classify(
                    text,
                    mode="subsubcategory",
                    subcategory=subcategory,
                )

        if self.buzzpoints:
            # automatically generate metadata for buzzpoint-migrator
            metadata = ""

        if not metadata and alternate_subcategory:
            metadata = f"{category} - {subcategory} - {alternate_subcategory}"

        if not metadata and not alternate_subcategory:
            metadata = f"{category} - {subcategory}"

        return category, subcategory, alternate_subcategory, metadata

    def parse_category_tag(self, text: str) -> tuple[str, str, str, str] | None:
        category_tag = regex.search(
            self.REGEX_CATEGORY_TAG,
            remove_formatting(text),
            flags=Parser.REGEX_FLAGS,
        )

        if not category_tag:
            return None

        category_tag = category_tag.group()
        category_tag = category_tag.strip().replace("\n", " ")
        metadata = category_tag[1:-1]

        subcategory = get_subcategory(category_tag)
        alternate_subcategory = get_alternate_subcategory(category_tag)
        category = SUBCAT_TO_CAT[subcategory] if subcategory else ""

        return category, subcategory, alternate_subcategory, metadata

    def parse_bonus_tags(
        self, text: str
    ) -> tuple[list[Literal["e", "m", "h"]], list[int]]:
        """
        Parse the bonus tags from the given text and extract the difficulties and values.
        If self.modaq or self.buzzpoints is true, the values will be set to 10 if no value is found.

        Args:
            text (str): The text to parse the bonus tags from.

        Returns:
            tuple[list[Literal["e", "m", "h"]], list[int]]: A tuple (difficulties, values)
        """

        tags = regex.findall(self.REGEX_BONUS_TAGS, text, flags=Parser.REGEX_FLAGS)
        difficultyModifiers = []
        values = []

        for tag in tags:
            for difficultyModifier in ["e", "m", "h"]:
                if difficultyModifier in tag.lower():
                    difficultyModifiers.append(difficultyModifier)
                    break

            for value in ["10", "15", "20", "5"]:
                if value in tag:
                    values.append(int(value))
                    break

        if len(values) == 0 and (self.modaq or self.buzzpoints):
            values = [10 for _ in range(len(tags))]

        return difficultyModifiers, values

    def preprocess_packet(self, packet_text: str) -> str:
        if self.modaq:
            packet_text = packet_text.replace('"', "\u0022")

        # remove spaces before first non-space character
        packet_text = regex.sub(r"^ +", "", packet_text, flags=Parser.REGEX_FLAGS)

        packet_text = packet_text + "\n0."
        # remove zero-width characters
        packet_text = packet_text.replace("", "").replace("​", "")
        # change soft hyphens to regular hyphens
        packet_text = packet_text.replace("\xad", "-")
        # change greek question mark to semicolon
        packet_text = packet_text.replace("\u037e", ";")  # Greek question mark

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

        # replace tabs and redundant spaces
        packet_text = packet_text.replace("\t", " ")
        packet_text = regex.sub(r" {2,}", " ", packet_text, flags=Parser.REGEX_FLAGS)

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
            r"^\(?(\d{1,2}|TB)\)", "1. ", packet_text, flags=Parser.REGEX_FLAGS
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

        # handle question number on a new line from the question text
        packet_text = regex.sub(
            r"(\d{1,2}\.) *\n", "\g<1>", packet_text, flags=Parser.REGEX_FLAGS
        )

        # clear lines that are all spaces
        packet_text = regex.sub(r"^\s*$", "", packet_text, flags=Parser.REGEX_FLAGS)

        # ensure ANSWER starts on a new line
        packet_text = regex.sub(
            r"(?<=.)(?=ANSWER:)", "\n", packet_text, flags=Parser.REGEX_FLAGS
        )

        # remove duplicate lines
        count = regex.findall(r"(.+)\n\1", packet_text, flags=Parser.REGEX_FLAGS)
        packet_text = regex.sub(
            r"([^\n]+)\n\1\n", "\g<1>\n", packet_text, flags=Parser.REGEX_FLAGS
        )
        if len(count) > 0:
            Logger.warning(f"Removed {len(count)} duplicate lines")

        # remove "Page X" lines
        packet_text = regex.sub(r"Page \d+( of \d+)?", "", packet_text, flags=Parser.REGEX_FLAGS)

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

        missing_directives = regex.search(
            "description acceptable", packet_text, flags=Parser.REGEX_FLAGS
        )
        missing_directives = (
            0 if missing_directives is None else len(missing_directives)
        )
        not_sanitized = self.modaq or self.buzzpoints

        for tossup in tossups:
            tossup_parsed = self.parse_tossup(tossup)
            data["tossups"].append(tossup_parsed)
            self.tossup_index += 1
            question_text = (
                tossup_parsed["question"]
                if not_sanitized
                else tossup_parsed["question_sanitized"]
            )
            missing_directives -= int("description acceptable" in question_text.lower())

        for bonus in bonuses:
            bonus_parsed = self.parse_bonus(bonus)
            data["bonuses"].append(bonus_parsed)
            self.bonus_index += 1
            leadin_text = (
                bonus_parsed["leadin"]
                if not_sanitized
                else bonus_parsed["leadin_sanitized"]
            )
            missing_directives -= int("description acceptable" in leadin_text.lower())
            for part in (
                bonus_parsed["parts"]
                if not_sanitized
                else bonus_parsed["parts_sanitized"]
            ):
                missing_directives -= int("description acceptable" in part.lower())

        if missing_directives > 0:
            Logger.warning(
                f"{missing_directives} 'description acceptable' directive(s) may not have parsed in this packet"
            )

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
    "-a",
    "--always-classify",
    is_flag=True,
    help="Always auto classify categories, even if category tag is detected.",
)
@click.option(
    "-b",
    "--buzzpoints",
    is_flag=True,
    help="Output in a format compatible with buzzpoints. Cannot be used with -m/--modaq.",
)
@click.option(
    "-c",
    "--classify-unknown",
    is_flag=True,
    default=True,
    show_default=True,
    help="Auto classify unrecognized categories in tags.",
)
@click.option(
    "-f",
    "--force-overwrite",
    is_flag=True,
    help="Overwrite existing files in output/ directory.",
)
@click.option(
    "-m",
    "--modaq",
    is_flag=True,
    help="Output in a format compatible with MODAQ. Cannot be used with -b/--buzzpoints.",
)
@click.option(
    "-p",
    "--auto-insert-powermarks",
    is_flag=True,
    help="Insert powermarks for questions that are bolded in power but do not have an explicit powermark.",
)
@click.option(
    "-s",
    "--space-powermarks",
    is_flag=True,
    help="Ensure powermarks are surrounded by spaces.",
)
def main(
    input_directory,
    output_directory,
    bonus_length,
    always_classify,
    buzzpoints,
    classify_unknown,
    force_overwrite,
    modaq,
    auto_insert_powermarks,
    space_powermarks,
):
    if buzzpoints and modaq:
        Logger.error("Cannot output in both buzzpoints and MODAQ formats")
        exit(1)

    ########## START OF PROMPTS ##########

    try:
        os.mkdir(output_directory)
    except FileExistsError:
        Logger.warning("Output directory already exists!")
        if force_overwrite:
            Logger.warning("Overwriting files in output directory")
        else:
            print(
                "Use -f/--force-overwrite to overwrite existing files in output directory"
            )
            exit(0)

    HAS_QUESTION_NUMBERS = input("Do you have question numbers? (y/n) ") == "y"
    HAS_CATEGORY_TAGS = input("Do you have category tags? (y/n) ") == "y"
    print("Using category tags" if HAS_CATEGORY_TAGS else "Using question classifier")

    ########## END OF PROMPTS ##########

    parser = Parser(
        HAS_QUESTION_NUMBERS,
        HAS_CATEGORY_TAGS,
        bonus_length,
        buzzpoints,
        modaq,
        auto_insert_powermarks,
        classify_unknown,
        space_powermarks,
        always_classify,
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
