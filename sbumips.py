import argparse
from pathlib import Path

from interpreter.interpreter import *
from lexer import MipsLexer
from mipsParser import MipsParser
from preprocess import walk, link, preprocess
from settings import settings

'''
https://github.com/sbustars/STARS

Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''


def init_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('filename', type=str, help='Input MIPS Assembly file.')

    p.add_argument('-a', '--assemble', help='Assemble code without running', action='store_true')
    p.add_argument('-d', '--debug', help='Enables debugging mode', action='store_true')
    p.add_argument('-g', '--garbage', help='Enables garbage data', action='store_true')
    p.add_argument('-n', '--max_instructions', help='Sets max number of instructions', type=int)
    p.add_argument('-i', '--disp_instr_count', help='Displays the total instruction count', action='store_true')
    p.add_argument('-w', '--warnings', help='Enables warnings', action='store_true')
    p.add_argument('-pa', type=str, nargs='+', help='Program arguments for the MIPS program')

    return p.parse_args()


def init_settings(args: argparse.Namespace) -> None:
    settings['assemble'] = args.assemble
    settings['debug'] = args.debug
    settings['garbage_memory'] = args.garbage
    settings['garbage_registers'] = args.garbage
    settings['disp_instr_count'] = args.disp_instr_count
    settings['warnings'] = args.warnings

    if args.max_instructions:
        settings['max_instructions'] = args.max_instructions


def assemble(filename: str) -> List:
    path = Path(filename)
    path.resolve()

    files = []
    eqv_dict = {}
    abs_to_rel = {}

    walk(path, files, eqv_dict, abs_to_rel, path.parent)
    contents = {}
    results = {}
    processed = {}
    for file in files:
        with file.open() as f:
            s = f.readlines()
            file = file.as_posix()

            contents[file] = ''.join(s)
            processed[file] = preprocess(contents[file], file, eqv_dict)

            lexer = MipsLexer(file)
            parser = MipsParser(contents[file], file)

            tokenized = lexer.tokenize(processed[file])
            results[file] = parser.parse(tokenized)

    if settings['assemble']:
        print('Program assembled successfully.')
        exit()

    og_text, text = link(files, contents, processed, abs_to_rel)
    parser = MipsParser(og_text, files[0])
    lexer = MipsLexer(files[0].as_posix())

    t = lexer.tokenize(text)
    return parser.parse(t)


if __name__ == '__main__':
    args = init_args()
    init_settings(args)

    pArgs = args.pa if args.pa else []

    try:
        result = assemble(args.filename)
        inter = Interpreter(result, pArgs)
        inter.interpret()

        if settings['disp_instr_count']:
            inter.out(f'\nInstruction count: {inter.instruction_count}')

    except Exception as e:
        if hasattr(e, 'message'):
            print(type(e).__name__ + ": " + e.message, file=sys.stderr)

        else:
            print(type(e).__name__ + ": " + str(e), file=sys.stderr)
