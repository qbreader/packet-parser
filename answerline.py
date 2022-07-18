from collections import Counter
import json
import re
from typing import List, Tuple

PEOPLE_INDICATORS = [
    'person',
    'leader',
    'figure',
    'country',
    'accountant',
    'actor',
    'actress',
    'air traffic controller',
    'architect',
    'artist',
    'attorney',
    'banker',
    'bartender',
    'barber',
    'bookkeeper',
    'builder',
    'businessman',
    'businesswoman',
    'businessperson',
    'butcher',
    'carpenter',
    'cashier',
    'chef',
    'coach',
    'dental hygienist',
    'dentist',
    'designer',
    'developer',
    'dietician',
    'doctor',
    'economist',
    'editor',
    'electrician',
    'engineer',
    'farmer',
    'filmmaker',
    'fisherman',
    'flight attendant',
    'jeweler',
    'judge',
    'lawyer',
    'mechanic',
    'musician',
    'nutritionist',
    'nurse',
    'optician',
    'painter',
    'pharmacist',
    'photographer',
    'physician',
    'pilot',
    'poet',
    'plumber',
    'police officer',
    'politician',
    'president',
    'professor',
    'programmer',
    'psychologist',
    'receptionist',
    'salesman',
    'salesperson',
    'saleswoman',
    'secretary',
    'singer',
    'surgeon',
    'teacher',
    'therapist',
    'translator',
    'translator',
    'undertaker',
    'veterinarian',
    'videographer',
    'waiter',
    'waitress',
    'writer']


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


def get_keyword(fragment: str) -> tuple:
    if fragment[:2] == 'or': 
        return 'or', '<b><u>', '</u></b>'
    if fragment[:6] == 'accept': 
        return 'accept', '<b><u>', '</u></b>'
    if fragment[:9] == 'prompt on': 
        return 'prompt on', '<u>', '</u>'
    if fragment[:6] == 'reject':
        return 'reject', '"', '"'
    if fragment[:26] == 'do not accept or prompt on':
        return 'do not accept or prompt on', '"', '"'
    if fragment[:13] == 'do not accept':
        return 'do not accept', '"', '"'
    return '', '', ''


def is_person(indicator: str) -> bool:
    return indicator in PEOPLE_INDICATORS


def process_piece(piece: str, acceptor: str, left_tag: str, right_tag: str, first: bool) -> Tuple[str, str]:
    piece = piece.strip()
    if len(piece) == 0: return '', ''
    if piece[0] == '"':
        piece = piece[1:]
    if piece[-1] == '"':
        piece = piece[:-1]

    if piece == 'equivalents': 
        return '', f' {acceptor} equivalents'

    for phrase in ['a ', 'an ', 'the ', 'more specific answers such as ', 'answers like ']:
        if piece[:len(phrase)] == phrase:
            piece = piece[len(phrase):].strip()
            return piece, f'{acceptor} {phrase}{left_tag}{piece}{right_tag}'

    for word in [' before ', ' after ', ' since ']:
        if word in piece:
            piece, after = piece.split(word)[0], piece.split(word)[1]
            piece = piece.strip()
            after = after.strip()
            return piece, f'{acceptor} {left_tag}{piece}{right_tag}{word}{after}'

    return piece, f'{acceptor if first else " or"} {left_tag}{piece}{right_tag}'


def process_question(question: str, answer: str) -> Tuple[str, List[str], List[str], List[str]]:
    """
    Processes the question and answer.
    Returns: `answer_formatted, acceptable, promptable, rejectable`.
    """
    answer_formatted = ''
    acceptable = []
    promptable = []
    rejectable = []

    main_answer, alternate_answer = split_main_alternate(answer)
    index = main_answer.rfind(' ')
    if is_person(get_indicator(question)) and not index == -1:
        before, main_answer = main_answer[:index], main_answer[index+1:]
        answer_formatted = f'{before} <b><u>{main_answer}</u></b>'
    else:
        answer_formatted += f'<b><u>{main_answer}</u></b>'
    if alternate_answer == '':
        return answer_formatted, acceptable, promptable, rejectable

    answer_formatted += ' ['
    answer_fragments = alternate_answer.split(';')
    for fragment in answer_fragments:
        fragment = fragment.strip()
        acceptor, left_tag, right_tag = get_keyword(fragment)
        if acceptor:
            first = True
            fragment = re.split(f' {acceptor} | or ', ' ' + fragment)
            for piece in fragment:
                piece, answer_text = process_piece(piece, acceptor, left_tag, right_tag, first)
                answer_formatted += answer_text
                if len(piece) == 0: continue

                first = False
                if acceptor in ['accept', 'or']:
                    acceptable.append(piece)
                if acceptor in ['prompt on']:
                    promptable.append(piece)
                if acceptor in ['reject', 'do not accept or prompt on']:
                    rejectable.append(piece)
            answer_formatted += '; '
        else:
            answer_formatted += f'{fragment}; '

    answer_formatted = answer_formatted[:-2] + ']'
    return answer_formatted, acceptable, promptable, rejectable


def split_main_alternate(answer) -> Tuple[str, str]:
    """
    Get the text between the brackets.
    """
    index1 = answer.find('[')
    index2 = answer.find(']')
    if index1 != -1 and index2 != -1:
        return answer[:index1].strip(), answer[index1+1:index2].strip()
    else:
        return answer, ''


f = open('packet.json')
data = json.load(f)

questions = data['tossups']

for question in questions:
    answer_formatted, _, _, _ = process_question(question['question'], question['answer'])
    print(answer_formatted)
