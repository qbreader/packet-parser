from collections import Counter
import json
import re


def get_indicator(text):
    indicators = ['']
    text = text.lower()
    text = text.split(' ')
    for i in range(len(text) - 1):
        if text[i] in ['this', 'these']:
            indicator = text[i+1]
            if indicator[-2:] == '\'s':
                indicator = indicator[:-2]
            if indicator[-1:] in ['\'', ',', '.']:
                indicator = indicator[:-1]

            indicators.append(indicator)

    return Counter(indicators).most_common(1)[0][0]


def split_main_alternate(answer):
    """
    Get the text between the brackets.
    """
    index1 = answer.find('[')
    index2 = answer.find(']')
    if index1 != -1 and index2 != -1:
        return answer[:index1].strip(), answer[index1+1:index2].strip()
    else:
        return None

f = open('packet.json')
data = json.load(f)

questions = data['tossups']

for question in questions:
    answer_formatted = ''
    index = question['answer'].find('[')
    if index == -1:
        main_answer = question['answer'].strip()
        print(f"{get_indicator(question['question'])}: {main_answer}")
        continue

    acceptable = []
    promptable = []
    rejectable = []
    main_answer, alternate_answer = split_main_alternate(question['answer'])
    answer_formatted += f'<b><u>{main_answer}</u></b> ['
    answer_fragments = alternate_answer.split(';')
    for fragment in answer_fragments:
        fragment = fragment.strip()
        if fragment[:2] == 'or': acceptor = 'or'
        if fragment[:6] == 'accept': acceptor = 'accept'
        if fragment[:9] == 'prompt on': acceptor = 'prompt on'
        if acceptor:
            fragment = ' ' + fragment
            fragment = re.split(f' {acceptor} | or ', fragment)
            first = False
            for piece in fragment:
                piece = piece.strip()
                if len(piece) == 0: continue
                if piece == 'equivalents': 
                    answer_formatted += f' or equivalents'
                    continue
                if piece.find('before') != -1:
                    before, after = piece[:piece.index('before')], piece[piece.index('before') + 6:]
                    before = before.strip()
                    after = after.strip()
                    answer_formatted += f'{acceptor} <u>{before}</u> before {after}'
                    continue
                if not first:
                    answer_formatted += f'{acceptor} <b><u>{piece}</u></b>'
                    first = True
                else:
                    answer_formatted += f' or <b><u>{piece}</u></b>'
                
                if acceptor in ['accept', 'or']:
                    acceptable.append(piece)
                if acceptor in ['prompt on']:
                    promptable.append(piece)
                if acceptor in ['reject', 'do not accept or prompt on']:
                    rejectable.append(piece)
            answer_formatted += '; '

        elif fragment[:6] == 'reject':
            answer_formatted += f'{fragment}; '
            fragment = fragment[6:].strip()
            if fragment[0] == '"':
                fragment = fragment[1:]
            if fragment[-1] == '"':
                fragment = fragment[:-1]
            rejectable.append(fragment)
        elif fragment[:26] == 'do not accept or prompt on':
            answer_formatted += f'{fragment}; '
            fragment = fragment[26:].strip()
            if fragment[0] == '"':
                fragment = fragment[1:]
            if fragment[-1] == '"':
                fragment = fragment[:-1]
            rejectable.append(fragment)
        else:
            answer_formatted += f'{fragment}; '
    answer_formatted = answer_formatted[:-2] + ']'
    print(f"{get_indicator(question['question'])}: {main_answer} [{alternate_answer}]")
    print(acceptable)
    print(promptable)
    print(rejectable)
    print(answer_formatted)