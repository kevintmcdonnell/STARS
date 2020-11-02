from typing import Dict

from constants import *
from settings import settings
from sly.lex import Lexer
import re

'''
Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''


def makeRegex() -> Dict[str, str]:
    ret = {}

    for k, opList in settings['pseudo_ops'].items():
        regex = ''

        for op in opList:
            regex += f'|{op}'
        ret[k] = regex[1:]

    return ret


def get_reg_value(reg: str) -> str:
    match = re.search(r'[ ,]', reg)

    if match:
        return reg[:match.start()]

    return reg


class MipsLexer(Lexer):
    tokens = {HALF, ALIGN, EQV, LABEL, ZERO_BRANCH, BRANCH, I_TYPE, LOADS_I,
              LOADS_F, R_TYPE3_F, R_TYPE2_F, COMPARE_F, BRANCH_F, CONVERT_F, MOVE_BTWN_F, MOVE_F, MOVE_COND_F,
              LOADS_R, J_TYPE, J_TYPE_R, R_TYPE3, SYSCALL, R_TYPE2, NOP, BREAK, MOVE, MOVE_COND,
              REG, F_REG, LABEL, NUMBER, STRING, CHAR, FLOAT_LITERAL,
              LPAREN, RPAREN, COMMA, COLON, LINE_MARKER,
              TEXT, DATA, WORD, BYTE, FLOAT, DOUBLE, ASCIIZ, ASCII, SPACE,
              PS_R_TYPE3, PS_R_TYPE2, PS_I_TYPE, PS_LOADS_I, PS_LOADS_A, PS_BRANCH, PS_ZERO_BRANCH}
    ignore = ' \t'
    pseudoOps = makeRegex()

    # Basic floating point instructions
    LOADS_F = r'\b(l|s)\.[sd]\b'
    R_TYPE3_F = r'\b(add|sub|mul|div)\.[sd]\b'
    R_TYPE2_F = r'\b(abs|ceil\.w|floor\.w|mov|neg|round\.w|trunc\.w|sqrt)\.[sd]\b'
    COMPARE_F = r'\b(c\.(eq|le|lt)\.[ds])\b'
    BRANCH_F = r'\b(bc1[ft])\b'
    CONVERT_F = r'\b(cvt\.(w\.[ds]|s\.[dw]|d\.[sw]))\b'
    MOVE_BTWN_F = r'\b(m[ft]c1)\b'
    MOVE_F = r'\b(mov[nz])\.[sd]\b'
    MOVE_COND_F = r'\b(mov[ft])\.[sd]\b'

    # Basic instructions
    R_TYPE3 = r'\b(and|addu?|mul|[xn]?or|sllv|srav|slt[u]?|sub[u]?|mov[nz])\b'
    R_TYPE2 = r'\b(div[u]?|mult[u]?|madd[u]?|msub[u]?|cl[oz])\b'

    MOVE = r'\b(m[tf]hi|m[tf]lo)\b'
    MOVE_COND = r'\b(mov[ft])\b'

    J_TYPE = r'\b(j|b|jal)\b'
    J_TYPE_R = r'\b(jalr|jr)\b'
    I_TYPE = r'\b(addi[u]?|andi|sr[al]|sll|sltiu?|xori|ori)\b'
    LOADS_R = r'\b(lb[u]?|lh[u]?|lw[lr]|lw|s[bhw]|sw[lr])\b'
    LOADS_I = r'\b(lui)\b'
    SYSCALL = r'\b(syscall)\b'
    BRANCH = r'\b(beq|bne)\b'
    ZERO_BRANCH = r'\b(bl[et]z|bg[te]z|bgezal|bltzal)\b'

    NOP = r'\b(nop)\b'
    BREAK = r'\b(break)\b'

    # Pseudo Instructions
    PS_R_TYPE3 = rf'\b({pseudoOps["R_TYPE3"]})\b'
    PS_R_TYPE2 = rf'\b({pseudoOps["R_TYPE2"]})\b'
    PS_I_TYPE = rf'\b({pseudoOps["I_TYPE"]})\b'
    PS_LOADS_I = rf'\b({pseudoOps["LOADS_I"]})\b'
    PS_LOADS_A = r'\b(la)\b'
    PS_BRANCH = rf'\b({pseudoOps["BRANCH"]})\b'
    PS_ZERO_BRANCH = rf'\b({pseudoOps["ZERO_BRANCH"]})\b'

    # Strings
    LABEL = r'[a-zA-Z_][a-zA-Z0-9_\.]*'
    STRING = r'"(.|\s)*?"'

    # Special symbols
    LPAREN = r'\('
    RPAREN = r'\)'
    COMMA = r','
    COLON = r':'

    # Directives
    TEXT = r'\.text'
    DATA = r'\.data'
    WORD = r'\.word'
    BYTE = r'\.byte'
    HALF = r'\.half'
    FLOAT = r'\.float'
    DOUBLE = r'\.double'
    ASCIIZ = r'\.asciiz'
    ASCII = r'\.ascii'
    SPACE = r'\.space'
    EQV = r'\.eqv .*? .*?(?=\x81)'
    ALIGN = r'\.align'

    def __init__(self, filename):
        self.filename = filename
        self.lineno = 1

    # \x81\x83
    @_(r'(\x81\x82|\x81\x83) ".*?" \d+')
    def LINE_MARKER(self, t):
        return t

    @_(r'[$](a[0123t]|s[01234567]|t[0123456789]|v[01]|ra|sp|fp|gp|zero|3[01]|[12]?\d) *,?')
    def REG(self, t):
        t.value = get_reg_value(t.value)
        return t

    @_(r'[$]f(3[01]|[12]?\d),?')
    def F_REG(self, t):
        t.value = get_reg_value(t.value)
        return t

    @_(r'[-+]?[0-9]*\.[0-9]+([eE][-+]?[0-9]+)?')
    def FLOAT_LITERAL(self, t):
        t.value = float(t.value)
        return t

    @_(r'-?(0[xX][0-9A-Fa-f]+|\d+)')
    def NUMBER(self, t):
        t.value = int(t.value, 0)
        return t

    @_(r"'(\\[\\0rnt']|.|\s)'")
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
        elif char == "\\'":
            char = '\''
        elif char == "\\\\":
            char = '\\'

        t.value = ord(char)
        return t

    @_(r'\#[^\x81\n]*')
    def ignore_comments(self, t):
        self.lineno += t.value.count('\n')

    # Line number tracking
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    @_(r'\.(include|globl)[^\n]*')
    def ignore_globl(self, t):
        # These were already taken care of during the preprocessing stage, so we don't need them
        self.lineno += t.value.count('\n')

    def error(self, t):
        raise SyntaxError(f'File {self.filename} Line {self.lineno}: Bad character {t.value[0]}')
