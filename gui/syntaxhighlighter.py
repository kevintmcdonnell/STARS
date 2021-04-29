from PySide2.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont
from PySide2.QtCore import Qt, QRegularExpression, QRegularExpressionMatchIterator
from lexer import MipsLexer

class HighlightingRule:
    def __init__(self, pattern, format):
        self.pattern = pattern
        self.format = format

class Highlighter(QSyntaxHighlighter):

    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(Qt.blue)

        patterns = [MipsLexer.LOADS_F, MipsLexer.R_TYPE3_F, MipsLexer.R_TYPE2_F, MipsLexer.COMPARE_F, MipsLexer.BRANCH_F, MipsLexer.CONVERT_F,
                         MipsLexer.MOVE_BTWN_F, MipsLexer.MOVE_F, MipsLexer.MOVE_COND_F, MipsLexer.R_TYPE3, MipsLexer.R_TYPE2, MipsLexer.MOVE,
                         MipsLexer.MOVE_COND, MipsLexer.J_TYPE, MipsLexer.J_TYPE_R, MipsLexer.I_TYPE, MipsLexer.LOADS_R, MipsLexer.LOADS_I, MipsLexer.SYSCALL,
                         MipsLexer.BREAK, MipsLexer.ZERO_BRANCH, MipsLexer.NOP, MipsLexer.BREAK, MipsLexer.PS_R_TYPE3, MipsLexer.PS_R_TYPE2, MipsLexer.PS_I_TYPE,
                         MipsLexer.PS_LOADS_I, MipsLexer.PS_LOADS_A, MipsLexer.PS_BRANCH, MipsLexer.PS_ZERO_BRANCH]
        self.rules = []
        for p in patterns:
            rule = HighlightingRule(QRegularExpression(p), keywordFormat)
            self.rules.append(rule)

        labelFormat = QTextCharFormat()
        labelFormat.setForeground(Qt.darkYellow)
        labelFormat.setFontWeight(QFont.Bold)
        self.rules.append(HighlightingRule(QRegularExpression(rf'{MipsLexer.LABEL}\s*:'), labelFormat))

        numberFormat = QTextCharFormat()
        numberFormat.setForeground(Qt.darkGreen)
        self.rules.append(HighlightingRule(QRegularExpression(r'\b(\d+|(0x[0-9A-Fa-f]+))\b'), numberFormat))

        stringFormat = QTextCharFormat()
        stringFormat.setForeground(Qt.darkBlue)
        self.rules.append(HighlightingRule(QRegularExpression(f'{MipsLexer.STRING}'), stringFormat))

        directiveFormat = QTextCharFormat()
        directiveFormat.setForeground(Qt.darkMagenta)
        directiveFormat.setFontWeight(QFont.Bold)
        d_patterns = [MipsLexer.TEXT, MipsLexer.DATA, MipsLexer.WORD, MipsLexer.BYTE, MipsLexer.HALF, MipsLexer.FLOAT, MipsLexer.DOUBLE, MipsLexer.ASCII, MipsLexer.ASCIIZ, MipsLexer.SPACE, MipsLexer.EQV, MipsLexer.ALIGN]

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(Qt.darkGray)
        self.rules.append(HighlightingRule(QRegularExpression(r'#.*'), commentFormat))
        for p in d_patterns:
            rule = HighlightingRule(QRegularExpression(p), directiveFormat)
            self.rules.append(rule)

        regFormat = QTextCharFormat()
        regFormat.setForeground(Qt.red)
        self.rules.append(HighlightingRule(QRegularExpression(r'\$\w+'), regFormat))


    def highlightBlock(self, text:str) -> None:
        for rule in self.rules:
            i = rule.pattern.globalMatch(text)
            while i.hasNext():
                m = i.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), rule.format)

        self.setCurrentBlockState(0)