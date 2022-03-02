punctuation = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
s = 'abcdefg...'

for ch in punctuation:
    s = s.replace(ch, '')

print(s.replace(punctuation, ''))