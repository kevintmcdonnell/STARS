from typing import Tuple, Dict

from constants import FILE_MARKER, LINE_MARKER
from interpreter.exceptions import *
from interpreter.interpreter import *
from settings import settings
from sly.lex import Lexer
from pathlib import Path


# Determine if the replacement string for eqv is valid
def isValid(s: str, lexer: Lexer) -> bool:
    restrictedTokens = settings['pseudo_ops'].keys()

    for attr in restrictedTokens:
        if re.search(getattr(lexer, attr), s):
            return False

    return True


def walk(filename: Path, files: List[Path], eqv: Dict[str, str], abs_to_rel: Dict[Path, str], lexer: Lexer, parent: Path) -> None:
    f = filename.open(mode='r', errors='ignore')

    # Patterns to detect if line is an .eqv or .include directive
    eq_pattern = re.compile(r'[.]eqv (.*?)? (.*)')
    incl_pattern = re.compile(r'[.]include "(.*?)"')

    files.append(filename)
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
            rel = incl_match.group(1)
            file = parent.joinpath(rel)
            file.resolve()

            abs_to_rel[file] = rel

            if file in files:
                f.close()
                raise FileAlreadyIncluded(f'{filename}, line number: {line_count}: {file} already included.')

            walk(file, files, eqv, abs_to_rel, lexer, parent)

    f.close()


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
    abs_to_rel = {}

    # Step 1: Do a depth-first search of the .include tree, gathering file names and
    # .eqv definitions along the way
    path = Path(filename)
    path.resolve()

    walk(path, files, eqv, abs_to_rel, lexer, path.parent)
    texts = [''] * len(files)
    original_text = {}

    # Step 2: Add file markers and line markers
    for i, filename in enumerate(files):
        file = filename.open(mode='r', errors='ignore')
        count = 1

        filename_fslash = filename.as_posix()
        original_text[filename_fslash] = file.readlines()
        first_line = True
        for line in original_text[filename_fslash]:
            line = line.strip()

            if line == '' or line[0] == '#':
                texts[i] += line + '\n'
            elif first_line:  # Beginning of a new file
                texts[i] += line + f' {FILE_MARKER} \"{filename_fslash}\" {count}\n'
                first_line = False
            else:
                texts[i] += line + f' {LINE_MARKER} \"{filename_fslash}\" {count}\n'

            count += 1

        file.close()

    # Step 3: Replace .include directives with the actual contents of the files
    text = texts[0]

    for filename, contents in zip(files, texts):
        if filename in abs_to_rel:
            pattern = rf'\.include "{abs_to_rel[filename]}".*?\n'
            text = re.sub(pattern, contents, text)

    newText = ''

    # Step 4: Do eqv substitution
    for line in text.split('\n'):
        line = line.strip()
        line = substitute(line, eqv)
        newText += (line + '\n')

    newText = newText.strip()
    return newText, original_text

def eqv(contents: Dict[str, str], eqv: Dict[str, str]) -> None:
    for k in contents.keys():
        newText = ''
        count = 1
        first_line = True
        for line in contents[k].split('\n'):
            line = line.strip()
            line = substitute(line, eqv)

            if line == '' or line[0] == '#':
                line = line + '\n'
            elif first_line:  # Beginning of a new file
                line = line + f' {FILE_MARKER} \"{k}\" {count}\n'
                first_line = False
            else:
                line = line + f' {LINE_MARKER} \"{k}\" {count}\n'

            count += 1
            newText += line

        newText = newText.strip()
        contents[k] = newText

def link(files: List[str], contents: Dict[str, str], abs_to_rel: Dict[str, str]):
    text = contents[files[0]]
    for name, content in zip(files, contents):
        if name in abs_to_rel:
            pattern = rf'\.include "{abs_to_rel[name]}".*?\n'
            text = re.sub(pattern, contents, text)
    return text