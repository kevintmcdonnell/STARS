from sly.lex import Lexer
from sly.yacc import Parser

from interpreter import Interpreter
import preprocess
from classes import *
from constants import *
from settings import settings
import argparse
from typing import Dict


def makeRegex() -> Dict[str, str]:
    ret = {}

    for k in settings['pseudo_ops'].keys():
        opList = settings['pseudo_ops'][k]
        regex = ''

        for op in opList:
            regex += ('|(' + op + ')')
        ret[k] = regex[1:]

    return ret


def get_upper_half(x: int) -> int:
    # Get the upper 16 bits of a 32 bit number.
    return (x >> 16) & 0xFFFF


class MipsLexer(Lexer):
    tokens = {HALF, ALIGN, EQV, LABEL, ZERO_BRANCH, BRANCH, I_TYPE, LOADS_I,
              LOADS_R, J_FUNCT, J_FUNCTR, R_FUNCT3, SYSCALL, R_FUNCT2, NOP, BREAK, MOVE, REG, LABEL, NUMBER, STRING, CHAR, LPAREN, RPAREN,
              COMMA, COLON, LINE_MARKER, TEXT, DATA, WORD, BYTE, ASCIIZ, ASCII, SPACE, INCLUDE, GLOBL,
              PS_R_FUNCT3, PS_R_FUNCT2, PS_I_TYPE, PS_LOADS_I, PS_LOADS_A, PS_BRANCH, PS_ZERO_BRANCH}
    ignore = ' \t'
    pseudoOps = makeRegex()

    # Basic instructions
    R_FUNCT3 = r'\b((and)|(addu?)|(mul)|([xn]?or)|(sllv)|(srav)|(slt[u]?)|(sub[u]?)|(mov[nz]))\b'
    R_FUNCT2 = r'\b((div[u]?)|(mult[u]?)|(madd[u]?)|(msub[u]?)|(cl[oz]))\b'

    MOVE = r'\b((m[tf]hi)|(m[tf]lo))\b'

    J_FUNCT = r'\b((j)|(b)|(jal))\b'
    J_FUNCTR = r'\b((jalr)|(jr))\b'
    I_TYPE = r'\b((addi[u]?)|(andi)|(sr[al])|(sll)|(sltiu?)|(xori)|(ori))\b'
    LOADS_R = r'\b((lb[u]?)|(lh[u]?)|(lw[lr])|(lw)|(s[bhw])|(sw[lr]))\b'
    LOADS_I = r'\b((lui))\b'
    SYSCALL = r'\bsyscall\b'
    BRANCH = r'\b((beq)|(bne))\b'
    ZERO_BRANCH = r'\b((bl[et]z)|(bg[te]z)|(bgezal)|(bltzal))\b'

    NOP = r'\bnop\b'
    BREAK = r'\bbreak\b'

    # Pseudo Instructions
    PS_R_FUNCT3 = r'\b(' + pseudoOps['R_FUNCT3'] + r')\b'
    PS_R_FUNCT2 = r'\b(' + pseudoOps['R_FUNCT2'] + r')\b'
    PS_I_TYPE = r'\b(' + pseudoOps['I_TYPE'] + r')\b'
    PS_LOADS_I = r'\b(' + pseudoOps['LOADS_I'] + r')\b'
    PS_LOADS_A = r'\bla\b'
    PS_BRANCH = r'\b(' + pseudoOps['BRANCH'] + r')\b'
    PS_ZERO_BRANCH = r'\b(' + pseudoOps['ZERO_BRANCH'] + r')\b'

    # Strings
    LABEL = r'[a-zA-Z_][a-zA-Z0-9_]*'
    STRING = r'"(.|\s)*?"'

    # Special symbols
    LPAREN = r'\('
    RPAREN = r'\)'
    COMMA = r','
    COLON = r':'

    # Reserved words
    TEXT = r'\.text'
    DATA = r'\.data'
    WORD = r'\.word'
    BYTE = r'\.byte'
    HALF = r'\.half'
    ASCIIZ = '\.asciiz'
    ASCII = '\.ascii'
    SPACE = r'\.space'
    EQV = r'\.eqv (.*?) (.*?(?=\x81))'
    INCLUDE = r'\.include'
    ALIGN = r'\.align'
    GLOBL = r'\.globl'

    @_(r'(\x81\x82)|(\x81\x83)')
    def LINE_MARKER(self, t):
        if t.value == FILE_MARKER:
            self.lineno = 1

        return t

    @_(r'[$]((0|(a[0123t])|(s[01234567])|(t[0123456789])|(v[01])|(ra)|(sp)|(fp)|(gp))|([123]?\d)),?')
    def REG(self, t):
        if t.value[-1] == ',':
            t.value = t.value[:-1]
        return t

    @_(r'(0x[0-9A-Fa-f]+)|(-?\d+)')
    def NUMBER(self, t):
        t.value = int(str(t.value), 0)
        return t

    @_(r"'(.|\s|\\[0rntfv])'")
    def CHAR(self, t):
        char = t.value[1: -1]

        if char == '\\0':
            char = '\0'
        elif char == '\\n':
            char = '\n'
        elif char == '\\r':
            char = '\r'
        elif char == '\\t':
            char = '\t'
        elif char == '\\f':
            char = '\t'
        elif char == '\\v':
            char = '\v'

        t.value = ord(char)
        return t

    # Line number tracking
    @_(r'\#[^\x81\n]*')
    def ignore_comments(self, t):
        pass

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        raise SyntaxError(f'Line {self.lineno}: Bad character {t.value[0]}')


######## PARSER ###############
class MipsParser(Parser):
    tokens = MipsLexer.tokens
    debugfile = 'parser.out'

    def __init__(self, lines):
        # self.lines = lines
        self.labels = {}
        self.lines = lines

    # Top level section (Data, Text)
    @_('sects')
    def program(self, p):
        return p.sects

    @_('sect', 'sect sects')
    def sects(self, p):
        if 'sects' in p._namemap:
            return p.sect + p.sects

        return p.sect

    @_('dSect', 'tSect', 'INCLUDE STRING filetag', 'GLOBL LABEL filetag')
    def sect(self, p):
        if 'INCLUDE' in p._namemap or 'GLOBL' in p._namemap:
            return []

        else:
            return p[0]

    @_('DATA filetag declarations')
    def dSect(self, p):
        return p.declarations

    @_('TEXT filetag instrs')
    def tSect(self, p):
        return p.instrs

    @_('LINE_MARKER STRING NUMBER')
    def filetag(self, p):
        file_name = p[1][1:-1]
        line_number = p[2]
        return FileTag(file_name, line_number)

    @_('LABEL COLON')
    def label(self, p):
        return Label(p.LABEL)

    # INSTRUCTIONS
    @_('instr filetag instrs', 'instr filetag', 'label instr filetag', 'label instr filetag instrs')
    def instrs(self, p):
        result = []

        if type(p.instr) == PseudoInstr:
            for i in range(len(p.instr.instrs)):
                p.instr.instrs[i].filetag = p.filetag
                p.instr.instrs[i].original_text = self.lines[p.filetag.file_name][p.filetag.line_no - 1]
                p.instr.instrs[i].is_from_pseudoinstr = True

        else:
            p.instr.filetag = p.filetag
            p.instr.original_text = self.lines[p.filetag.file_name][p.filetag.line_no - 1]
            p.instr.is_from_pseudoinstr = False

        if 'label' in p._namemap:
            result.append(p.label)

        if 'instr' in p._namemap:
            result.append(p.instr)

        if 'instrs' in p._namemap:
            result += p.instrs

        return result

    @_('branch', 'rType', 'syscall', 'jType', 'iType', 'move', 'label', 'nop', 'breakpoint')
    def instr(self, p):
        return p[0]

    @_('I_TYPE REG REG NUMBER', 'I_TYPE REG REG CHAR')
    def iType(self, p):
        return IType(p.I_TYPE, [p[1], p[2]], p[3])

    @_('R_FUNCT3 REG REG REG')
    def rType(self, p):
        return RType(p[0], [p[1], p[2], p[3]])

    @_('R_FUNCT2 REG REG')
    def rType(self, p):
        return RType(p[0], [p[1], p[2]])

    @_('J_FUNCT LABEL', 'J_FUNCTR REG')
    def jType(self, p):
        if 'LABEL' in p._namemap:
            return JType(p[0], Label(p[1]))

        return JType(p[0], p[1])

    @_('LOADS_I REG NUMBER', 'LOADS_I REG CHAR')
    def iType(self, p):
        return LoadImm(p[0], p[1], p[2])

    @_('LOADS_R REG NUMBER LPAREN REG RPAREN', 'LOADS_R REG LPAREN REG RPAREN')
    def iType(self, p):
        if 'LPAREN' in p._namemap:
            if 'NUMBER' in p._namemap:
                return LoadMem(p[0], p.REG0, p.REG1, p.NUMBER)
            else:
                return LoadMem(p[0], p.REG0, p.REG1, 0)

        return None

    @_('MOVE REG')
    def move(self, p):
        return Move(p[0], p[1])

    @_('BRANCH REG REG LABEL', 'ZERO_BRANCH REG LABEL')
    def branch(self, p):
        if len(p) == 4:
            return Branch(p[0], p[1], p[2], Label(p[3]))

        else:
            return Branch(p[0], p[1], '$0', Label(p[2]))

    @_('SYSCALL')
    def syscall(self, p):
        return Syscall()

    @_('NOP')
    def nop(self, p):
        return Nop()

    @_('BREAK', 'BREAK NUMBER')
    def breakpoint(self, p):
        if len(p) == 2:
            return Breakpoint(p.NUMBER)

        return Breakpoint()

    # PSEUDO INSTRUCTIONS
    @_('PS_I_TYPE REG REG NUMBER', 'PS_I_TYPE REG REG CHAR')
    def iType(self, p):
        instrs = []
        val = p[3]

        if p[0] == 'rol':
            instrs.append(IType('srl', ['$at', p.REG1], 32 - val))
            instrs.append(IType('sll', [p.REG0, p.REG1], val))
            instrs.append(RType('or', [p.REG0, p.REG0, '$at']))
            return PseudoInstr('rol', instrs)
        elif p[0] == 'ror':
            instrs.append(IType('sll', ['$at', p.REG1], 32 - val))
            instrs.append(IType('srl', [p.REG0, p.REG1], val))
            instrs.append(RType('or', [p.REG0, p.REG0, '$at']))
            return PseudoInstr('ror', instrs)

        return None

    @_('PS_R_FUNCT3 REG REG REG')
    def rType(self, p):
        instrs = []

        if p[0] == 'seq':
            instrs.append(RType('subu', [p.REG0, p.REG1, p.REG2]))
            instrs.append(IType('ori', ['$at', '$0'], 1))
            instrs.append(RType('sltu', [p.REG0, p.REG0, '$at']))
            return PseudoInstr('seq', instrs)

        elif p[0] == 'sne':
            instrs.append(RType('subu', [p.REG0, p.REG1, p.REG2]))
            instrs.append(RType('sltu', [p.REG0, '$0', p.REG0]))
            return PseudoInstr('sne', instrs)

        elif p[0] == 'sge':
            instrs.append(RType('slt', [p.REG0, p.REG1, p.REG2]))
            instrs.append(IType('ori', ['$at', '$0'], 1))
            instrs.append(RType('subu', [p.REG0, '$at', p.REG0]))
            return PseudoInstr('sge', instrs)

        elif p[0] == 'sgeu':
            instrs.append(RType('sltu', [p.REG0, p.REG1, p.REG2]))
            instrs.append(IType('ori', ['$at', '$0'], 1))
            instrs.append(RType('subu', [p.REG0, '$at', p.REG0]))
            return PseudoInstr('sgeu', instrs)

        elif p[0] == 'sgt':
            instrs.append(RType('slt', [p.REG0, p.REG2, p.REG1]))
            return PseudoInstr('sgt', instrs)

        elif p[0] == 'sgtu':
            instrs.append(RType('sltu', [p.REG0, p.REG2, p.REG1]))
            return PseudoInstr('sgtu', instrs)

        elif p[0] == 'sle':
            instrs.append(RType('slt', [p.REG0, p.REG2, p.REG1]))
            instrs.append(IType('ori', ['$at', '$0'], 1))
            instrs.append(RType('subu', [p.REG0, '$at', p.REG0]))
            return PseudoInstr('sle', instrs)

        elif p[0] == 'sleu':
            instrs.append(RType('sltu', [p.REG0, p.REG2, p.REG1]))
            instrs.append(IType('ori', ['$at', '$0'], 1))
            instrs.append(RType('subu', [p.REG0, '$at', p.REG0]))
            return PseudoInstr('sleu', instrs)

        elif p[0] == 'rolv':
            instrs.append(RType('subu', ['$at', '$0', p.REG2]))
            instrs.append(RType('srlv', ['$at', p.REG1, '$at']))
            instrs.append(RType('sllv', [p.REG0, p.REG1, p.REG2]))
            instrs.append(RType('or', [p.REG0, p.REG0, '$at']))
            return PseudoInstr('rolv', instrs)

        elif p[0] == 'rorv':
            instrs.append(RType('subu', ['$at', '$0', p.REG2]))
            instrs.append(RType('sllv', ['$at', p.REG1, '$at']))
            instrs.append(RType('srlv', [p.REG0, p.REG1, p.REG2]))
            instrs.append(RType('or', [p.REG0, p.REG0, '$at']))
            return PseudoInstr('rorv', instrs)

        return None

    @_('PS_R_FUNCT2 REG REG')
    def rType(self, p):
        if p[0] == 'move':
            instr = RType('addu', [p.REG0, '$0', p.REG1])
            return PseudoInstr('move', [instr])

        elif p[0] == 'neg':
            instr = RType('sub', [p.REG0, '$0', p.REG1])
            return PseudoInstr('neg', [instr])

        elif p[0] == 'not':
            instr = RType('nor', [p.REG0, p.REG1, '$0'])
            return PseudoInstr('not', [instr])

        elif p[0] == 'abs':
            instr = []
            instr.append(IType('sra', ['$at', p.REG1], 31))
            instr.append(RType('xor', [p.REG0, '$at', p.REG1]))
            instr.append(RType('subu', [p.REG0, p.REG0, '$at']))
            return PseudoInstr('abs', instr)

        return None

    @_('PS_LOADS_I REG NUMBER', 'PS_LOADS_I REG CHAR')
    def iType(self, p):
        if p[0] == 'li':
            instrs = []
            val = p[2]

            if 0 <= val < HALF_SIZE:
                instrs.append(IType('ori', [p.REG, '$0'], val))
            else:
                instrs.append(LoadImm('lui', '$at', get_upper_half(val)))
                instrs.append(IType('ori', [p.REG, '$at'], val & 0xFFFF))

            return PseudoInstr('li', instrs)

        return None

    @_('PS_LOADS_A REG LABEL')
    def iType(self, p):
        instrs = []
        instrs.append(LoadImm('lui', '$at', 0))
        instrs.append(IType('ori', [p.REG, '$at'], 0))

        pseudoInstr = PseudoInstr('la', instrs)
        pseudoInstr.label = Label(p.LABEL)
        return pseudoInstr

    @_('LOADS_R REG LABEL')
    def iType(self, p):
        # If it has a label, it's a pseudoinstruction
        instrs = []
        instrs.append(LoadImm('lui', '$at', 0))
        instrs.append(LoadMem(p[0], p.REG, '$at', 0))

        pseudoInstr = PseudoInstr(p[0], instrs)
        pseudoInstr.label = Label(p.LABEL)
        return pseudoInstr

    @_('PS_BRANCH REG REG LABEL', 'PS_ZERO_BRANCH REG LABEL')
    def branch(self, p):
        if len(p) == 4:
            instr = []
            if p[0] == 'bge':
                instr.append(RType('slt', ['$at', p[1], p[2]]))
                instr.append(Branch('beq', '$at', '$0', Label(p[3])))
                return PseudoInstr('bge', instr)
            elif p[0] == 'bgeu':
                instr.append(RType('sltu', ['$at', p[1], p[2]]))
                instr.append(Branch('beq', '$at', '$0', Label(p[3])))
                return PseudoInstr('bgeu', instr)
            elif p[0] == 'bgt':
                instr.append(RType('slt', ['$at', p[2], p[1]]))
                instr.append(Branch('bne', '$at', '$0', Label(p[3])))
                return PseudoInstr('bgt', instr)
            elif p[0] == 'bgtu':
                instr.append(RType('sltu', ['$at', p[2], p[1]]))
                instr.append(Branch('bne', '$at', '$0', Label(p[3])))
                return PseudoInstr('bgtu', instr)
            elif p[0] == 'ble':
                instr.append(RType('slt', ['$at', p[2], p[1]]))
                instr.append(Branch('beq', '$at', '$0', Label(p[3])))
                return PseudoInstr('ble', instr)
            elif p[0] == 'bleu':
                instr.append(RType('sltu', ['$at', p[2], p[1]]))
                instr.append(Branch('beq', '$at', '$0', Label(p[3])))
                return PseudoInstr('bleu', instr)
            elif p[0] == 'blt':
                instr.append(RType('slt', ['$at', p[1], p[2]]))
                instr.append(Branch('bne', '$at', '$0', Label(p[3])))
                return PseudoInstr('blt', instr)
            elif p[0] == 'bltu':
                instr.append(RType('sltu', ['$at', p[1], p[2]]))
                instr.append(Branch('bne', '$at', '$0', Label(p[3])))
                return PseudoInstr('bltu', instr)
            else:
                return None
        else:
            instr = []
            if p[0] == 'beqz':
                instr.append(Branch('beq', p.REG, '$0', Label(p[2])))
                return PseudoInstr('beqz', instr)
            elif p[0] == 'bnez':
                instr.append(Branch('bne', p.REG, '$0', Label(p[2])))
                return PseudoInstr('bnez', instr)
            else:
                return None

    # DECLARATIONS
    @_('declaration filetag declarations', 'declaration filetag')
    def declarations(self, p):
        if p.declaration:
            p.declaration[0].filetag = p.filetag

        result = p.declaration

        if len(p) == 3:
            result += p.declarations

        return result

    @_('label ASCIIZ STRING', 'label WORD nums', 'label BYTE chars', 'label ASCII STRING', 'label SPACE nums', 'label HALF nums',
       'ASCIIZ STRING', 'WORD nums', 'BYTE chars', 'ASCII STRING', 'SPACE nums', 'HALF nums', 'EQV', 'ALIGN NUMBER')
    def declaration(self, p):
        if 'label' in p._namemap:
            return [Declaration(p.label, p[1], p[2])]

        elif len(p) > 1:  # Not eqv
            return [Declaration(None, p[0], p[1])]

        # Eqv
        return []

    @_('NUMBER', 'NUMBER COMMA nums', 'NUMBER nums')
    def nums(self, p):
        result = [p.NUMBER]

        if len(p) > 1:
            result += p.nums

        return result

    @_('CHAR', 'CHAR COMMA chars', 'CHAR chars', 'NUMBER', 'NUMBER COMMA chars', 'NUMBER chars')
    def chars(self, p):
        result = [p[0]]

        if len(p) > 1:
            result += p[-1]

        return result

    def error(self, p):
        message = ''

        if p:
            message = f'Unexpected {p}'

        raise SyntaxError(message)


def start():
    p = argparse.ArgumentParser()
    p.add_argument('filename', type=str, help='Input MIPS Assembly file.')

    p.add_argument('-d', '--debug', help='Enables debugging mode', action='store_true')
    p.add_argument('-g', '--garbage', help='Enables garbage data', action='store_true')
    p.add_argument('-n', '--max_instructions', help='Sets max number of instructions', type=int)
    p.add_argument('-i', '--disp_instr_count', help='Displays the total instruction count', action='store_true')
    p.add_argument('-w', '--warnings', help='Enables warnings', action='store_true')
    p.add_argument('-pa', type=str, nargs='+', help='Program arguments for the MIPS program')

    try:
        args = p.parse_args()
        pArgs = []

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

        lexer = MipsLexer()
        data, lines = preprocess.preprocess(args.filename, lexer)
        parser = MipsParser(lines)

        r1 = lexer.tokenize(data)
        result = parser.parse(r1)
        inter = Interpreter(result, pArgs)
        inter.interpret()

        if settings['disp_instr_count']:
            print(f'\nInstruction count: {inter.instruction_count}')

    except Exception as e:
        if hasattr(e, 'message'):
            print(type(e).__name__ + ": " + e.message)

        else:
            print(type(e).__name__ + ": " + str(e))


if __name__ == '__main__':
    start()
