import re
from exceptions import *
from settings import settings
from constants import FILE_MARKER, LINE_MARKER
from sly.lex import Lexer
from typing import List, Tuple, Dict

# list of token regex names in MipsLexer that are restricted words
restrictedTokens = settings['pseudo_ops'].keys()
eq = re.compile(r'[.]eqv (.*?)? (.*)')
fi = re.compile(r'[.]include "(.*?)"')


def setStartLine(x: int) -> None:
    global startLine
    startLine = x


def isValid(s: str, lexer: Lexer) -> bool:
    for attr in restrictedTokens:
        if re.search(getattr(lexer, attr), s):
            return False
    return True


def walk(filename: str, files: List[str], eqv: List[List[str]], lexer: Lexer) -> Tuple[List, List]:
    f = open(filename, 'r')
    files.append(filename)
    line_count = 0
    for s in f.readlines():
        line_count += 1
        s = s.strip()
        s = s.split('#')[0]
        b = fi.match(s)
        eqMatch = eq.match(s)
        if eqMatch:
            if isValid(eqMatch.group(1), lexer):
                eqv.append(['\\b' + eqMatch.group(1) + '\\b', eqMatch.group(2)])
            else:
                f.close()
                raise InvalidEQVException('%s: line %d: %s is a restricted word and cannot be replaced using eqv.' %(filename, line_count, eqMatch.group(1)))
        elif b:
            file = b.group(1)
            if file in files:
                f.close()
                raise FileAlreadyIncludedException(filename + ', line number: ' + str(line_count) + ': ' + file + "already included.")
            walk(file, files, eqv, lexer)
    f.close()
    return files, eqv


def preprocess(filename: str, lexer: Lexer) -> Tuple[str, Dict[str, List[str]]]:
    files = []
    eqv = []
    files, eqv = walk(filename, files, eqv, lexer)
    texts = [''] * len(files)
    lines = {}

    for i in range(len(files)):
        file = open(files[i])
        count = 1
        lines[files[i]] = file.readlines()

        for line in lines[files[i]]:
            line = line.strip()

            if line == "" or line[0] == "#":
                texts[i] += line + "\n"
            elif count == 1:  # Beginning of a new file
                texts[i] += line + f' {FILE_MARKER} \"{files[i]}\" {count}\n'
            else:
                texts[i] += line + f' {LINE_MARKER} \"{files[i]}\" {count}\n'
            count += 1

        file.close()

    text = texts[0]
    for i in range(len(files)):
        text = re.sub(r'\.include "' + files[i] + '".*?\n', texts[i], text)

    newText = ''

    for line in text.split('\n'):
        line = line.strip()
        for e in eqv:
            if not re.search('eqv', line) and not re.search(r'".*?' + e[0] + r'.*?"', line) and not re.search(r'#.*?' + e[0] + r'.*?', line):
                line = re.sub(e[0], e[1], line)
        newText += (line + "\n")
    newText = newText[:-2]  # removes 2 lingering newlines
    return newText, lines
