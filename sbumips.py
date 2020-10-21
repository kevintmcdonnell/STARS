import argparse

from interpreter.interpreter import *
from lexer import MipsLexer
from mipsParser import MipsParser
from preprocess import preprocess, walk, link, eqv
from settings import settings
from pathlib import Path

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('filename', type=str, help='Input MIPS Assembly file.')

    p.add_argument('-a', '--assemble', help='Assemble code without running', action='store_true')
    p.add_argument('-d', '--debug', help='Enables debugging mode', action='store_true')
    p.add_argument('-g', '--garbage', help='Enables garbage data', action='store_true')
    p.add_argument('-n', '--max_instructions', help='Sets max number of instructions', type=int)
    p.add_argument('-i', '--disp_instr_count', help='Displays the total instruction count', action='store_true')
    p.add_argument('-w', '--warnings', help='Enables warnings', action='store_true')
    p.add_argument('-pa', type=str, nargs='+', help='Program arguments for the MIPS program')

    args = p.parse_args()
    pArgs = []

    if args.assemble:
        settings['assemble'] = True
    if args.debug:
        settings['debug'] = True
    if args.garbage:
        settings['garbage_memory'] = True
        settings['garbage_registers'] = True
    if args.disp_instr_count:
        settings['disp_instr_count'] = True
    if args.warnings:
        settings['warnings'] = True
    if args.max_instructions:
        settings['max_instructions'] = args.max_instructions
    if args.pa:
        pArgs = args.pa

    try:
        lexer = MipsLexer()
        files = []
        path = Path(args.filename)
        path.resolve()
        eqv_dict = {}
        abs_to_rel = {}
        walk(path, files, eqv_dict, abs_to_rel, lexer, path.parent)
        contents = {}
        for file in files:
            with file.open() as f:
                s = f.readlines()
                contents[file] = ''.join(s)
                eqv(contents, eqv_dict)
                parser = MipsParser(contents[file], file)
                tokenized = lexer.tokenize(contents[file])
                result = parser.parse(tokenized)

        if settings['assemble']:
            print('Program assembled successfully.')
            exit()

        result = link(files, contents, abs_to_rel)
        inter = Interpreter(result, pArgs)
        inter.interpret()

        if settings['disp_instr_count']:
            print(f'\nInstruction count: {inter.instruction_count}')

    except Exception as e:
        if hasattr(e, 'message'):
            print(type(e).__name__ + ": " + e.message, file=sys.stderr)

        else:
            print(type(e).__name__ + ": " + str(e), file=sys.stderr)
