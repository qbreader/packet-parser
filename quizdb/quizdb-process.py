import json
import os


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def xyz(a):
    try:
        a["round"] = a["round"].split()[0]
        return 100 * int(a["round"]) + a["number"]
    except:
        return -1 + a["number"]


ADD_UNDERLINING = input("Add underlining to bolding (y/n) ") == "y"

f = open("quizdb.json")
data = json.load(f)["data"]

rounds = list(
    set([_["round"] for _ in data["tossups"]] + [_["round"] for _ in data["bonuses"]])
)


DIRECTORY = "output/"
os.mkdir(DIRECTORY)

for round in rounds:
    output = {"tossups": [], "bonuses": []}
    for a in data["tossups"]:
        if a["round"] == round:
            b = {}
            b["question"] = a["text"]
            b["answer"] = a["answer"]
            if ADD_UNDERLINING:
                b["formatted_answer"] = (
                    a["formatted_answer"]
                    .replace("<strong>", "<b><u>")
                    .replace("</strong>", "</u></b>")
                )
            else:
                b["formatted_answer"] = (
                    a["formatted_answer"]
                    .replace("<strong>", "<b>")
                    .replace("</strong>", "</b>")
                )
            if "name" in a["subcategory"]:
                b["subcategory"] = a["subcategory"]["name"]
            if "name" in a["category"]:
                b["category"] = a["category"]["name"]
            output["tossups"].append(b)

    for a in data["bonuses"]:
        if a["round"] == round:
            b = {}
            b["leadin"] = a["leadin"]
            b["answers"] = a["answers"]
            if ADD_UNDERLINING:
                b["formatted_answers"] = [
                    _.replace("<strong>", "<b><u>").replace("</strong>", "</u></b>")
                    for _ in a["formatted_answers"]
                ]
            else:
                b["formatted_answers"] = [
                    _.replace("<strong>", "<b>").replace("</strong>", "</b>")
                    for _ in a["formatted_answers"]
                ]
            b["parts"] = a["texts"]
            if "name" in a["subcategory"]:
                b["subcategory"] = a["subcategory"]["name"]
            if "name" in a["category"]:
                b["category"] = a["category"]["name"]
            output["bonuses"].append(b)

    print(
        f'Found {len(output["tossups"]):2} tossups and {len(output["bonuses"]):2} bonuses in round {bcolors.OKBLUE}{round}{bcolors.ENDC}'
    )
    g = open(f"{DIRECTORY}{round}.json", "w")
    json.dump(output, g)
