import re
from exceptions import *
from settings import settings
from constants import FILE_MARKER, LINE_MARKER
from sly.lex import Lexer
from typing import List, Tuple, Dict


# Determine if the replacement string for eqv is valid
def isValid(s: str, lexer: Lexer) -> bool:
    restrictedTokens = settings['pseudo_ops'].keys()

    for attr in restrictedTokens:
        if re.search(getattr(lexer, attr), s):
            return False

    return True


def walk(filename: str, files: List[str], eqv: List[List[str]], lexer: Lexer) -> Tuple[List, List]:
    f = open(filename, 'r')

    # Replace backslashes with two backslashes for regex to work properly
    filename_re = re.sub(r'\\', r'\\\\', filename)

    # Patterns to detect if line is an .eqv or .include directive
    eq_pattern = re.compile(r'[.]eqv (.*?)? (.*)')
    incl_pattern = re.compile(r'[.]include "(.*?)"')

    files.append(filename_re)
    line_count = 0

    for line in f.readlines():
        line_count += 1

        # Ignore comments
        line = line.split('#')[0]

        incl_match = incl_pattern.match(line)
        eq_match = eq_pattern.match(line)

        if eq_match:
            original = eq_match.group(1)
            substitution = eq_match.group(2)

            if isValid(original, lexer):
                eqv.append([rf'\b{original}\b', substitution])

            else:
                f.close()
                raise InvalidEQV(f'{filename}: line {line_count}: {original} is a restricted word and cannot be replaced using eqv.')

        elif incl_match:
            file = incl_match.group(1)

            if file in files:
                f.close()
                raise FileAlreadyIncluded(filename + ', line number: ' + str(line_count) + ': ' + file + "already included.")

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
        pattern = r'\.include "' + files[i] + '".*?\n'
        text = re.sub(pattern, texts[i], text)

    newText = ''

    for line in text.split('\n'):
        line = line.strip()

        for e in eqv:
            def replace_func(match):
                # Get the index of the capture group that was matched
                group = match.lastindex

                # If it's the desired word and it's not in comments or strings, do the substitution
                if group == 4:
                    return e[1]

                # Otherwise, just ignore it
                else:
                    return match.group(group)

            # 1st group: Capture anything inside of double quotes
            # 2nd group: Capture anything after #
            # 3rd group: Capture anything after line marker
            # 4th group: Capture the word to replace
            # We don't actually care about the first 3 groups. We just have it so that we can exclude them from eqv substitution.
            eqv_pattern = r'("[^"]+")|(#.*)|(\x81.*)|(\bword\b)'

            # Do the substitution. We provide a custom substitution function.
            line = re.sub(eqv_pattern, replace_func, line)

        newText += (line + "\n")

    newText = newText.strip()
    return newText, lines
