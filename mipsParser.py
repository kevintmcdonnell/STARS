from constants import *
from interpreter.interpreter import *
from lexer import MipsLexer
from sly.yacc import Parser

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


def get_upper_half(x: int) -> int:
    # Get the upper 16 bits of a 32 bit number.
    return (x >> 16) & 0xFFFF


class MipsParser(Parser):
    tokens = MipsLexer.tokens
    debugfile = 'parser.out'

    def __init__(self, original_text, filename):
        self.labels = {}
        self.original_text = original_text.split('\n')
        self.filename = filename

    # Top level section (Data, Text)
    @_('sects')
    def program(self, p):
        return p.sects

    @_('sect', 'sect sects')
    def sects(self, p):
        if 'sects' in p._namemap:
            return p.sect + p.sects

        return p.sect

    @_('dSect', 'tSect')
    def sect(self, p):
        return p[0]

    @_('DATA filetag declarations')
    def dSect(self, p):
        return p.declarations

    @_('TEXT filetag instrs')
    def tSect(self, p):
        return p.instrs

    @_('LINE_MARKER')
    def filetag(self, p):
        x = p[0].split()
        file_name = x[1]
        line_number = int(x[2])
        self.filename = x[1]
        return FileTag(file_name, line_number)

    @_('LABEL COLON')
    def label(self, p):
        return Label(p.LABEL)

    # INSTRUCTIONS
    @_('instr filetag instrs', 'instr filetag', 'label instr filetag', 'label instr filetag instrs')
    def instrs(self, p):
        result = []

        if type(p.instr) is PseudoInstr:
            for i in range(len(p.instr.instrs)):
                p.instr.instrs[i].filetag = p.filetag
                p.instr.instrs[i].original_text = p.instr.operation
                p.instr.instrs[i].is_from_pseudoinstr = True

        else:
            p.instr.filetag = p.filetag
            p.instr.original_text = self.original_text[p.filetag.line_no - 1]
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

    @_('R_TYPE3 REG REG REG', 'R_TYPE3_F F_REG F_REG F_REG')
    def rType(self, p):
        return RType(p[0], [p[1], p[2], p[3]])

    @_('R_TYPE2 REG REG', 'R_TYPE2_F F_REG F_REG')
    def rType(self, p):
        return RType(p[0], [p[1], p[2]])

    @_('J_TYPE LABEL', 'J_TYPE_R REG')
    def jType(self, p):
        if 'LABEL' in p._namemap:
            return JType(p[0], Label(p[1]))

        return JType(p[0], p[1])

    @_('LOADS_I REG NUMBER', 'LOADS_I REG CHAR')
    def iType(self, p):
        return LoadImm(p[0], p[1], p[2])

    @_('LOADS_R REG NUMBER LPAREN REG RPAREN', 'LOADS_R REG LPAREN REG RPAREN')
    def iType(self, p):
        if 'NUMBER' in p._namemap:
            return LoadMem(p[0], p.REG0, p.REG1, p.NUMBER)
        else:
            return LoadMem(p[0], p.REG0, p.REG1, 0)

    @_('MOVE REG')
    def move(self, p):
        return Move(p[0], p[1])

    @_('MOVE_COND REG REG', 'MOVE_COND REG REG NUMBER')
    def iType(self, p):
        if len(p) == 3:
            return MoveCond(p.MOVE_COND, p.REG0, p.REG1, 0)

        return MoveCond(p.MOVE_COND, p.REG0, p.REG1, p.NUMBER)

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

    # FLOATING POINT INSTRUCTIONS
    @_('LOADS_F F_REG NUMBER LPAREN REG RPAREN', 'LOADS_F F_REG LPAREN REG RPAREN')
    def iType(self, p):
        if 'NUMBER' in p._namemap:
            return LoadMem(p[0], p.F_REG, p.REG, p.NUMBER)
        else:
            return LoadMem(p[0], p.F_REG, p.REG, 0)

    @_('COMPARE_F F_REG F_REG', 'COMPARE_F NUMBER F_REG F_REG', 'COMPARE_F NUMBER COMMA F_REG F_REG')
    def iType(self, p):
        if len(p) == 3:
            return Compare(p.COMPARE_F, p.F_REG0, p.F_REG1, 0)

        return Compare(p.COMPARE_F, p.F_REG0, p.F_REG1, p.NUMBER)

    @_('CONVERT_F F_REG F_REG')
    def iType(self, p):
        return Convert(p.CONVERT_F, p.F_REG0, p.F_REG1)

    @_('BRANCH_F LABEL', 'BRANCH_F NUMBER LABEL', 'BRANCH_F NUMBER COMMA LABEL')
    def branch(self, p):
        if len(p) == 2:
            return BranchFloat(p[0], Label(p[1]), 0)

        return BranchFloat(p[0], Label(p.LABEL), p.NUMBER)

    @_('MOVE_BTWN_F REG F_REG')
    def iType(self, p):
        return MoveFloat(p.MOVE_BTWN_F, [p.REG, p.F_REG])

    @_('MOVE_F F_REG F_REG REG')
    def rType(self, p):
        return MoveFloat(p.MOVE_F, [p.F_REG0, p.F_REG1, p.REG])

    @_('MOVE_COND_F F_REG F_REG', 'MOVE_COND_F F_REG F_REG NUMBER')
    def iType(self, p):
        if len(p) == 3:
            return MoveCond(p.MOVE_COND_F, p.F_REG0, p.F_REG1, 0)

        return MoveCond(p.MOVE_COND_F, p.F_REG0, p.F_REG1, p.NUMBER)

    # PSEUDO INSTRUCTIONS
    @_('PS_I_TYPE REG REG NUMBER', 'PS_I_TYPE REG REG CHAR')
    def iType(self, p):
        instrs = []
        val = p[3]

        if p[0] == 'rol':
            instrs.append(IType('srl', ['$at', p.REG1], 32 - val))
            instrs.append(IType('sll', [p.REG0, p.REG1], val))
            instrs.append(RType('or', [p.REG0, p.REG0, '$at']))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)
        elif p[0] == 'ror':
            instrs.append(IType('sll', ['$at', p.REG1], 32 - val))
            instrs.append(IType('srl', [p.REG0, p.REG1], val))
            instrs.append(RType('or', [p.REG0, p.REG0, '$at']))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        return None

    @_('PS_R_TYPE3 REG REG REG')
    def rType(self, p):
        instrs = []

        if p[0] == 'seq':
            instrs.append(RType('subu', [p.REG0, p.REG1, p.REG2]))
            instrs.append(IType('ori', ['$at', '$0'], 1))
            instrs.append(RType('sltu', [p.REG0, p.REG0, '$at']))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        elif p[0] == 'sne':
            instrs.append(RType('subu', [p.REG0, p.REG1, p.REG2]))
            instrs.append(RType('sltu', [p.REG0, '$0', p.REG0]))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        elif p[0] == 'sge':
            instrs.append(RType('slt', [p.REG0, p.REG1, p.REG2]))
            instrs.append(IType('ori', ['$at', '$0'], 1))
            instrs.append(RType('subu', [p.REG0, '$at', p.REG0]))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        elif p[0] == 'sgeu':
            instrs.append(RType('sltu', [p.REG0, p.REG1, p.REG2]))
            instrs.append(IType('ori', ['$at', '$0'], 1))
            instrs.append(RType('subu', [p.REG0, '$at', p.REG0]))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        elif p[0] == 'sgt':
            instrs.append(RType('slt', [p.REG0, p.REG2, p.REG1]))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        elif p[0] == 'sgtu':
            instrs.append(RType('sltu', [p.REG0, p.REG2, p.REG1]))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        elif p[0] == 'sle':
            instrs.append(RType('slt', [p.REG0, p.REG2, p.REG1]))
            instrs.append(IType('ori', ['$at', '$0'], 1))
            instrs.append(RType('subu', [p.REG0, '$at', p.REG0]))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        elif p[0] == 'sleu':
            instrs.append(RType('sltu', [p.REG0, p.REG2, p.REG1]))
            instrs.append(IType('ori', ['$at', '$0'], 1))
            instrs.append(RType('subu', [p.REG0, '$at', p.REG0]))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        elif p[0] == 'rolv':
            instrs.append(RType('subu', ['$at', '$0', p.REG2]))
            instrs.append(RType('srlv', ['$at', p.REG1, '$at']))
            instrs.append(RType('sllv', [p.REG0, p.REG1, p.REG2]))
            instrs.append(RType('or', [p.REG0, p.REG0, '$at']))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        elif p[0] == 'rorv':
            instrs.append(RType('subu', ['$at', '$0', p.REG2]))
            instrs.append(RType('sllv', ['$at', p.REG1, '$at']))
            instrs.append(RType('srlv', [p.REG0, p.REG1, p.REG2]))
            instrs.append(RType('or', [p.REG0, p.REG0, '$at']))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instrs)

        return None

    @_('PS_R_TYPE2 REG REG')
    def rType(self, p):
        if p[0] == 'move':
            instr = RType('addu', [p.REG0, '$0', p.REG1])
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]}', [instr])

        elif p[0] == 'neg':
            instr = RType('sub', [p.REG0, '$0', p.REG1])
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]}', [instr])

        elif p[0] == 'not':
            instr = RType('nor', [p.REG0, p.REG1, '$0'])
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]}', [instr])

        elif p[0] == 'abs':
            instr = []
            instr.append(IType('sra', ['$at', p.REG1], 31))
            instr.append(RType('xor', [p.REG0, '$at', p.REG1]))
            instr.append(RType('subu', [p.REG0, p.REG0, '$at']))
            return PseudoInstr(f'{p[0]} {p[1]} {p[2]}', instr)

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

            return PseudoInstr(f'{p[0]} {p[1]} {p[2]}', instrs)

        return None

    @_('PS_LOADS_A REG LABEL')
    def iType(self, p):
        instrs = []
        instrs.append(LoadImm('lui', '$at', 0))
        instrs.append(IType('ori', [p.REG, '$at'], 0))

        pseudoInstr = PseudoInstr(f'{p[0]} {p[1]} {p[2]}', instrs)
        pseudoInstr.label = Label(p.LABEL)
        return pseudoInstr

    @_('LOADS_R REG LABEL')
    def iType(self, p):
        # If it has a label, it's a pseudoinstruction
        instrs = [LoadImm('lui', '$at', 0), LoadMem(p[0], p.REG, '$at', 0)]

        pseudoInstr = PseudoInstr(f'{p[0]} {p[1]} {p[2]}', instrs)
        pseudoInstr.label = Label(p.LABEL)
        return pseudoInstr

    @_('PS_BRANCH REG REG LABEL', 'PS_ZERO_BRANCH REG LABEL')
    def branch(self, p):
        if len(p) == 4:
            instr = []
            if p[0] == 'bge':
                instr.append(RType('slt', ['$at', p[1], p[2]]))
                instr.append(Branch('beq', '$at', '$0', Label(p[3])))
                return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instr)
            elif p[0] == 'bgeu':
                instr.append(RType('sltu', ['$at', p[1], p[2]]))
                instr.append(Branch('beq', '$at', '$0', Label(p[3])))
                return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instr)
            elif p[0] == 'bgt':
                instr.append(RType('slt', ['$at', p[2], p[1]]))
                instr.append(Branch('bne', '$at', '$0', Label(p[3])))
                return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instr)
            elif p[0] == 'bgtu':
                instr.append(RType('sltu', ['$at', p[2], p[1]]))
                instr.append(Branch('bne', '$at', '$0', Label(p[3])))
                return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instr)
            elif p[0] == 'ble':
                instr.append(RType('slt', ['$at', p[2], p[1]]))
                instr.append(Branch('beq', '$at', '$0', Label(p[3])))
                return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instr)
            elif p[0] == 'bleu':
                instr.append(RType('sltu', ['$at', p[2], p[1]]))
                instr.append(Branch('beq', '$at', '$0', Label(p[3])))
                return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instr)
            elif p[0] == 'blt':
                instr.append(RType('slt', ['$at', p[1], p[2]]))
                instr.append(Branch('bne', '$at', '$0', Label(p[3])))
                return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instr)
            elif p[0] == 'bltu':
                instr.append(RType('sltu', ['$at', p[1], p[2]]))
                instr.append(Branch('bne', '$at', '$0', Label(p[3])))
                return PseudoInstr(f'{p[0]} {p[1]} {p[2]} {p[3]}', instr)
            else:
                return None
        else:
            instr = []
            if p[0] == 'beqz':
                instr.append(Branch('beq', p.REG, '$0', Label(p[2])))
                return PseudoInstr(f'{p[0]} {p[1]} {p[2]}', instr)
            elif p[0] == 'bnez':
                instr.append(Branch('bne', p.REG, '$0', Label(p[2])))
                return PseudoInstr(f'{p[0]} {p[1]} {p[2]}', instr)
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

    @_('LABEL COLON ASCIIZ STRING', 'LABEL COLON WORD nums', 'LABEL COLON BYTE chars', 'LABEL COLON ASCII STRING', 'LABEL SPACE nums',
       'LABEL COLON HALF nums',
       'LABEL COLON FLOAT floats', 'LABEL COLON DOUBLE floats',
       'ASCIIZ STRING', 'WORD nums', 'BYTE chars', 'ASCII STRING', 'SPACE nums', 'HALF nums',
       'FLOAT floats', 'DOUBLE floats', 'EQV', 'ALIGN NUMBER')
    def declaration(self, p):
        if 'LABEL' in p._namemap:
            return [Declaration(p.LABEL, p[2], p[3])]

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

    @_('FLOAT_LITERAL', 'FLOAT_LITERAL COMMA floats', 'FLOAT_LITERAL floats')
    def floats(self, p):
        result = [p.FLOAT_LITERAL]

        if len(p) > 1:
            result += p.floats

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
            message = f"Unexpected '{p.value}'"
            if self.filename:
                message += f' on {self.filename}:{p.lineno}'

        raise SyntaxError(message)
