from PySide2.QtWidgets import QPlainTextEdit, QTextEdit, QCompleter, QMainWindow, QAction, QApplication, QTabWidget, QFileDialog, QPushButton, QWidget
from PySide2.QtGui import QKeySequence, QTextCursor, QFocusEvent, QKeyEvent, QGuiApplication, QCursor, QPainter, QColor, QTextFormat
from PySide2.QtCore import Qt, QFile, QStringListModel, QSize, QRect
from lexer import MipsLexer
from gui.syntaxhighlighter import Highlighter

from os import pathsep

'''
Line Number Code Editor adapted from https://doc.qt.io/qt-5/qtwidgets-widgets-codeeditor-example.html
'''
# Internal counter for tracking number of new files
NEWFILE_COUNT = 1

class QLineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

class TextEdit(QPlainTextEdit):

    def __init__(self, parent=None, name='', text='', completer=None, textChanged=None, theme=[]):
        super().__init__(parent)
        self.setPlainText(text)
        self.completer = completer
        self.new_file = False
        if name == '':
            global NEWFILE_COUNT
            name = f'main{NEWFILE_COUNT}.asm'
            NEWFILE_COUNT += 1
            self.new_file = True
        self.name = name
        if textChanged:
            self.textChanged.connect(textChanged)
        if theme:
            self.theme = theme # [Line_number, Line_number_box, Current_Line_Highlight]
        print(self.theme)
        self.lineNumberArea = QLineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        max_value = max(1, self.blockCount())
        space = 5 + self.fontMetrics().width('9') * len(str(max_value))
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(self.theme[2])
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(self.theme[1]))
        # For line wrapping
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.setPen(QColor(self.theme[0]))
                painter.drawText(0, top, self.lineNumberArea.width(), height, Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def setCompleter(self, completer: QCompleter) -> None:
        if self.completer:
            self.completer.activated.disconnect()

        self.completer = completer
        if not completer:
            return

        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

        self.completer.activated.connect(self.insertCompletion)

    def getCompleter(self) -> QCompleter:
        return self.completer

    def insertCompletion(self, completion):
        if self.completer.widget() != self:
            return
        tc = self.textCursor()
        toadd = completion.split()[0]
        extra = len(toadd) - len(self.completer.completionPrefix())
        if extra == 0:
            return
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(toadd[-extra:])
        self.setTextCursor(tc)

    def textUnderCorsor(self) -> str:
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def focusInEvent(self, e: QFocusEvent) -> None:
        if self.completer:
            self.completer.setWidget(self)
        super(TextEdit, self).focusInEvent(e)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if self.completer and self.completer.popup().isVisible():
            if e.key() in [Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab]:
                e.ignore()
                return
        isShortcut = (e.modifiers() & Qt.ControlModifier) and (e.key() == Qt.Key_E)
        if not self.completer or not isShortcut:
            super(TextEdit, self).keyPressEvent(e)

        ctrlOrShift = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        if not self.completer or (ctrlOrShift and len(e.text()) == 0):
            return

        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        hasModifier = (e.modifiers() != Qt.NoModifier) and not ctrlOrShift
        completionPrefix = self.textUnderCorsor()

        if not isShortcut and (hasModifier or len(e.text()) == 0 or len(completionPrefix) < 2 or e.text()[-1] in eow):
            self.completer.popup().hide()
            return

        if completionPrefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completionPrefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)

    def getFilename(self) -> str:
        return self.name.split('/')[-1]

    def is_new(self) -> bool:
        return self.new_file

    def set_new(self, value: bool) -> None:
        self.new_file = value

    def set_theme(self, theme) -> None:
        self.theme = theme
        self.cursorPositionChanged.emit()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()

        self.files = {} # filename -> (dirty: bool, path: str)
        self.new_files = set()
        self.highlighter = {}

        self.count = 1
        self.len = 0
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        nt = QPushButton('+')
        nt.clicked.connect(self.new_tab)
        self.tabs.setCornerWidget(nt)

        self.completer = QCompleter(self)
        self.completer.setModel(self.modelFromFile(r"C:\Users\18605\PycharmProjects\sbumips\gui\wordslist.txt"))
        self.completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setWrapAround(False)

        self.setCentralWidget(self.tabs)
        self.resize(500, 300)
        self.setWindowTitle("Test Completer")

        self.new_tab()

        self.init_menu()

        self.show()

    def init_menu(self):
        bar = self.menuBar()

        file_ = bar.addMenu("File")
        open_ = QAction("Open", self)
        open_.triggered.connect(self.open_file)
        file_.addAction(open_)
        save_ = QAction("Save", self)
        save_.triggered.connect(self.save_file)
        file_.addAction(save_)

        tab = bar.addMenu("Tab")
        open_tab = QAction("Open", self)
        open_tab.triggered.connect(self.new_tab)
        tab.addAction(open_tab)

        save_all = QAction("Save All", self)
        save_all.triggered.connect(self.save_all)
        bar.addAction(save_all)

    def save_file(self, wid=None, ind=None):
        if not wid:
            wid = self.tabs.currentWidget()
        if not ind:
            ind = self.tabs.currentIndex()
        key = wid.name
        to_write = wid.toPlainText()
        f = None
        try:
            if key in self.files:
                f = open(key, 'w+')

                f.write(to_write)
                f.close()
                self.files[key] = False
            else:
                filename = QFileDialog.getSaveFileName(self, 'Save', f'{key}', options=QFileDialog.DontUseNativeDialog)
                if len(filename) < 2 or filename[0] is None:
                    return
                key = filename[0]
                f = open(key, 'w+')

                f.write(to_write)
                f.close()
                wid.name = filename[0]
                n = filename[0].split('/')[-1]
                self.tabs.setTabText(ind, n)
                self.files[key] = False
        except:
            if f:
                f.close()
            return

    def open_file(self):
        try:
            filename = QFileDialog.getOpenFileName(self, 'Open', '', options=QFileDialog.DontUseNativeDialog)
        except:
            return

        if not filename or len(filename[0]) == 0:
            return

        s = []
        with open(filename[0]) as f:
            s = f.readlines()
        wid = TextEdit(name=filename[0])
        wid.textChanged.connect(self.update_dirty)
        wid.setCompleter(self.completer)
        wid.setPlainText(''.join(s))
        n = filename[0].split('/')[-1]
        if not filename[0] in self.files:
            self.files[filename] = False
            self.new_tab(wid=wid, name=n)

    def close_tab(self, i):
        if self.tabs.widget(i).name in self.files:
            self.files.pop(self.tabs.widget(i).name)
        self.tabs.removeTab(i)
        self.len -= 1

    def new_tab(self, wid=None, name=''):
        self.count += 1
        self.len += 1
        if len(name) == 0:
            name = f'main{"" if self.count == 1 else self.count-1}.asm'
        if not wid:
            wid = TextEdit(name=name)
            wid.setCompleter(self.completer)
        self.tabs.addTab(wid, name)
        self.highlighter[name] = Highlighter(wid.document())

    def update_dirty(self):
        w = self.tabs.currentWidget()
        self.files[w.name] = True

    def save_all(self):
        for i in range(self.len):
            self.save_file(wid=self.tabs.widget(i), ind=i)

    def modelFromFile(self, filename):
        f = QFile(filename)
        if not f.open(QFile.ReadOnly):
            return QStringListModel(self.completer)

        QGuiApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        words = []
        while not f.atEnd():
            line = f.readLine()
            if len(line) > 0:
                s = str(line.trimmed(), encoding='ascii')
                words.append(s)

        QGuiApplication.restoreOverrideCursor()

        return QStringListModel(words, self.completer)

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow(app)
    app.exec_()