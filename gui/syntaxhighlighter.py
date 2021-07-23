from PySide2.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PySide2.QtCore import Qt, QRegularExpression, QRegularExpressionMatchIterator

from constants import PATTERN_EXPRESSIONS

class HighlightingRule:
    def __init__(self, name, pattern, format):
        self.type = name
        self.pattern = pattern
        self.format = format

    def set_format(self, format):
        self.format = format

class Highlighter(QSyntaxHighlighter):

    def __init__(self, parent=None, theme=None):
        super(Highlighter, self).__init__(parent)

        self.rules = []
        for name, patterns in PATTERN_EXPRESSIONS.items():
            format = QTextCharFormat()
            if type(patterns) is list:
                for pattern in patterns:
                    self.rules.append(HighlightingRule(name, QRegularExpression(pattern), format))
            else:
                self.rules.append(HighlightingRule(name, QRegularExpression(patterns), format))
        self.update_highlight(theme)

    def update_highlight(self, theme):
        new_formats = {} # generate new formats
        for name, attributes in theme.items():
            format = QTextCharFormat()
            if "color" in attributes:
                format.setForeground(QColor(attributes["color"]))
            if "font-weight" in attributes:
                format.setFontWeight(attributes["font-weight"])
            new_formats[name] = format
        for rule in self.rules: # update formats
            if rule.type in new_formats:
                rule.set_format(new_formats[rule.type])

    def highlightBlock(self, text:str) -> None:
        for rule in self.rules:
            i = rule.pattern.globalMatch(text)
            while i.hasNext():
                m = i.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), rule.format)

        self.setCurrentBlockState(0)