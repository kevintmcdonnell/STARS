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


def walk(filename: str, files: List[str], eqv: Dict[str, str], lexer: Lexer) -> Tuple[List, Dict]:
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
                eqv[rf'\b{original}\b'] = substitution

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


# Perform macro substitutions of a single line of code.
def substitute(line: str, eqv: Dict[str, str]) -> str:
    for original, substitution in eqv.items():
        def replace_func(match):
            # Get the index of the capture group that was matched
            group = match.lastindex

            # If it's the desired word and it's not in comments or strings, do the substitution
            if group == 4:
                return substitution

            # Otherwise, just ignore it
            else:
                return match.group(group)

        # 1st group: Capture anything inside of double quotes
        # 2nd group: Capture anything after #
        # 3rd group: Capture anything after line marker
        # 4th group: Capture the word to replace
        # We don't actually care about the first 3 groups. We just have it so that we can exclude them from eqv substitution.
        eqv_pattern = rf'("[^"]+")|(#.*)|(\x81.*)|(\b{original}\b)'

        # Do the substitution. We provide a custom substitution function.
        line = re.sub(eqv_pattern, replace_func, line)

    return line


def preprocess(filename: str, lexer: Lexer) -> Tuple[str, Dict[str, List[str]]]:
    files = []
    eqv = {}

    # Step 1: Do a depth-first search of the .include tree, gathering file names and
    # .eqv definitions along the way
    files, eqv = walk(filename, files, eqv, lexer)
    texts = [''] * len(files)
    original_text = {}

    # Step 2: Add file markers and line markers
    for i, filename in enumerate(files):
        file = open(filename)
        count = 1
        original_text[filename] = file.readlines()

        for line in original_text[filename]:
            line = line.strip()

            if line == "" or line[0] == "#":
                texts[i] += line + "\n"
            elif count == 1:  # Beginning of a new file
                texts[i] += line + f' {FILE_MARKER} \"{filename}\" {count}\n'
            else:
                texts[i] += line + f' {LINE_MARKER} \"{filename}\" {count}\n'

            count += 1

        file.close()

    # Step 3: Replace .include directives with the actual contents of the files
    text = texts[0]

    for filename, contents in zip(files, texts):
        pattern = r'\.include "' + filename + '".*?\n'
        text = re.sub(pattern, contents, text)

    newText = ''

    # Step 4: Do eqv substitution
    for line in text.split('\n'):
        line = line.strip()
        line = substitute(line, eqv)
        newText += (line + "\n")

    newText = newText.strip()
    return newText, original_text
