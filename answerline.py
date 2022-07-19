from collections import Counter
import json
import os
import re
from typing import List, Tuple

"""
Answerlines have the following form:
ANSWER: {main_answer} [{alternate_answer}]
ANSWER: {main_answer} [{answer_fragment}; {answer_fragment}; ... {answer_fragment}]
ANSWER: {main_answer} [{acceptor} {piece} or {piece} ...; {acceptor} {piece} or {piece} ...]

Example:
ANSWER: {sailor} [{or} {al-Ba\u1e25riyy}; {accept} answers like {seaman} or {mariner} or {pirate}; {accept} {The Story of the Shipwrecked Sailor}; {prompt on} {merchant}]
"""

PACKET_DIRECTORY = 'packets'

DESCRIPTIVE_WORDS = [' before ', ' after ', ' since ']
META_ANSWERS = ['equivalents', 'word forms']
PREFIX_PHRASES = ['a ', 'an ', 'the ', 'more specific answers such as ', 'answers like ', 'any description mentioning ', 'word forms like ']
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
    'author',
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
            if indicator[-2:] in ['\'s', '’s']:
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
    acceptor = acceptor if first else " or"
    piece = piece.strip()
    if len(piece) == 0: return '', ''
    if piece[0] == '"':
        piece = piece[1:]
    if piece[-1] == '"':
        piece = piece[:-1]

    if piece in META_ANSWERS:
        return '', f'{acceptor} {piece}'

    for phrase in PREFIX_PHRASES:
        if piece[:len(phrase)] == phrase:
            piece = piece[len(phrase):].strip()
            return piece, f'{acceptor} {phrase}{left_tag}{piece}{right_tag}'

    for word in DESCRIPTIVE_WORDS:
        if word in piece:
            piece, after = piece.split(word)[0], piece.split(word)[1]
            piece = piece.strip()
            after = after.strip()
            return piece, f'{acceptor} {left_tag}{piece}{right_tag}{word}{after}'

    return piece, f'{acceptor} {left_tag}{piece}{right_tag}'


def process_question(question: str, answer: str) -> dict:
    """
    Processes the question and answer.
    Returns: `answer_formatted, acceptable, promptable, rejectable, metadata`.
    """
    answer_formatted = ''
    acceptable = []
    promptable = []
    rejectable = []

    main_answer, alternate_answer, metadata = split_main_alternate_metadata(answer)
    acceptable.append(main_answer)
    index = main_answer.rfind(' ')
    if is_person(get_indicator(question)) and not index == -1:
        before, main_answer = main_answer[:index], main_answer[index+1:]
        answer_formatted = f'{before} <b><u>{main_answer}</u></b>'
    else:
        answer_formatted += f'<b><u>{main_answer}</u></b>'
    if alternate_answer == '':
        return {
        'answer_formatted': answer_formatted,
        'acceptable': acceptable,
        'promptable': promptable,
        'rejectable': rejectable,
        'metadata': metadata
    }

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
    return {
        'answer_formatted': answer_formatted,
        'acceptable': acceptable,
        'promptable': promptable,
        'rejectable': rejectable,
        'metadata': metadata
    }


def split_main_alternate_metadata(answer) -> Tuple[str, str, str]:
    """
    Get the text between the brackets.
    """
    index1 = answer.find('[')
    index2 = answer.find(']')
    index3 = answer.find('<')
    index4 = answer.find('>')
    index5 = answer.find('(')
    index6 = answer.find(')')
    metadata = ''
    if index3 != -1 and index4 != -1:
        metadata += answer[index3+1:index4]
    if index5 != -1 and index6 != -1:
        metadata += answer[index5+1:index6]
    if index3 == -1: index3 = len(answer)
    if index5 == -1: index5 = len(answer)
    if index3 != -1 or index5 != -1:
        answer = answer[:min(index3, index5)]
    if index1 != -1 and index2 != -1:
        return answer[:index1].strip(), answer[index1+1:index2].strip(), metadata
    else:
        return answer.strip(), '', metadata.strip()

for (dirpath, dirnames, filenames) in os.walk(PACKET_DIRECTORY):
    for filename in filenames:
        if filename == '.DS_Store': continue

        f = open(dirpath + '/' + filename)
        packet = json.load(f)

        if 'tossups' in packet:
            for i, tossup in enumerate(packet['tossups']):
                try:
                    result = process_question(tossup['question'], tossup['answer'])
                    packet['tossups'][i]['answer_formatted'] = result['answer_formatted']
                    packet['tossups'][i]['acceptable'] = result['acceptable']
                    packet['tossups'][i]['promptable'] = result['promptable']
                    packet['tossups'][i]['rejectable'] = result['rejectable']
                    packet['tossups'][i]['metadata'] = result['metadata']
                except: 
                    print(f'Error processing tossup {i} in {dirpath}/{filename}')
                    print(tossup)
                    continue

        if 'bonuses' in packet:
            for i, bonus in enumerate(packet['bonuses']):
                try:
                    answers_formatted = []
                    acceptables = []
                    promptables = []
                    rejectables = []
                    metadata = []
                    for j in range(3):
                        result = process_question(bonus['parts'][j], bonus['answers'][j])
                        answers_formatted.append(result['answer_formatted'])
                        acceptables.append(result['acceptable'])
                        promptables.append(result['promptable'])
                        rejectables.append(result['rejectable'])
                        metadata.append(result['metadata'])
                    packet['bonuses'][i]['answers_formatted'] = answers_formatted
                    packet['bonuses'][i]['acceptable'] = acceptables
                    packet['bonuses'][i]['promptable'] = promptables
                    packet['bonuses'][i]['rejectable'] = rejectables
                    packet['bonuses'][i]['metadata'] = metadata
                except:
                    print(f'Error processing bonus {i} in {dirpath}/{filename}')
                    print(bonus)
                    continue
        f = open(dirpath + '/' + filename, 'w')
        json.dump(packet, f)