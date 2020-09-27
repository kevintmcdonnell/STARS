from typing import Dict

from constants import *
from settings import settings
from sly.lex import Lexer


def makeRegex() -> Dict[str, str]:
    ret = {}

    for k, opList in settings['pseudo_ops'].items():
        regex = ''

        for op in opList:
            regex += f'|{op}'
        ret[k] = regex[1:]

    return ret


class MipsLexer(Lexer):
    tokens = {HALF, ALIGN, EQV, LABEL, ZERO_BRANCH, BRANCH, I_TYPE, LOADS_I,
              LOADS_R, J_TYPE, J_TYPE_R, R_TYPE3, SYSCALL, R_TYPE2, NOP, BREAK, MOVE,
              REG, F_REG, LABEL, NUMBER, STRING, CHAR,
              LPAREN, RPAREN, COMMA, COLON, LINE_MARKER,
              TEXT, DATA, WORD, BYTE, FLOAT, DOUBLE, ASCIIZ, ASCII, SPACE,
              PS_R_TYPE3, PS_R_TYPE2, PS_I_TYPE, PS_LOADS_I, PS_LOADS_A, PS_BRANCH, PS_ZERO_BRANCH}
    ignore = ' \t'
    pseudoOps = makeRegex()

    # Basic instructions
    R_TYPE3 = r'\b(and|addu?|mul|[xn]?or|sllv|srav|slt[u]?|sub[u]?|mov[nz])\b'
    R_TYPE2 = r'\b(div[u]?|mult[u]?|madd[u]?|msub[u]?|cl[oz])\b'

    MOVE = r'\b(m[tf]hi|m[tf]lo)\b'

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

    # Basic floating point instructions

    # Pseudo Instructions
    PS_R_TYPE3 = rf'\b({pseudoOps["R_TYPE3"]})\b'
    PS_R_TYPE2 = rf'\b({pseudoOps["R_TYPE2"]})\b'
    PS_I_TYPE = rf'\b({pseudoOps["I_TYPE"]})\b'
    PS_LOADS_I = rf'\b({pseudoOps["LOADS_I"]})\b'
    PS_LOADS_A = r'\b(la)\b'
    PS_BRANCH = rf'\b({pseudoOps["BRANCH"]})\b'
    PS_ZERO_BRANCH = rf'\b({pseudoOps["ZERO_BRANCH"]})\b'

    # Strings
    LABEL = r'[a-zA-Z_][a-zA-Z0-9_]*'
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

    @_(r'(\x81\x82|\x81\x83)')
    def LINE_MARKER(self, t):
        if t.value == FILE_MARKER:
            # Reset line number
            self.lineno = 1

        return t

    @_(r'[$](a[0123t]|s[01234567]|t[0123456789]|v[01]|ra|sp|fp|gp|3[01]|[12]?\d),?')
    def REG(self, t):
        if t.value[-1] == ',':
            t.value = t.value[:-1]
        return t

    @_(r'[$]f(3[01]|[12]?\d),?')
    def F_REG(self, t):
        if t.value[-1] == ',':
            t.value = t.value[:-1]
        return t

    @_(r'(0x[0-9A-Fa-f]+|-?\d+)')
    def NUMBER(self, t):
        t.value = int(t.value, 0)
        return t

    @_(r'[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?')
    def FLOAT(self, t):
        t.value = float(t.value)

    @_(r"'(.|\s|\\[0rnt])'")
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

        t.value = ord(char)
        return t

    @_(r'\#[^\x81\n]*')
    def ignore_comments(self, t):
        pass

    # Line number tracking
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    @_(r'\.(include|globl)[^\n]*')
    def ignore_directives(self, t):
        # These were already taken care of during the preprocessing stage, so we don't need them
        pass

    def error(self, t):
        raise SyntaxError(f'Line {self.lineno}: Bad character {t.value[0]}')
