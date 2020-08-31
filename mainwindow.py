from PySide2.QtWidgets import QMainWindow, QAction, QApplication, QFileDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QWidget, QLineEdit, QTextEdit
from PySide2.QtCore import Signal, Qt
from PySide2.QtGui import QFont, QTextCharFormat, QTextCursor

from sbumips import MipsLexer, MipsParser
from preprocess import preprocess
from interpreter import Interpreter
from settings import settings
from constants import REGS

from threading import Thread


class MainWindow(QMainWindow):

    def __init__(self, app):
        super().__init__()
        self.app = app

        settings['gui'] = True
        settings['debug'] = True
        self.result = None
        self.intr = None
        self.cur_file = None
        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("STARS")
        self.lay = QHBoxLayout()
        self.left = QVBoxLayout()
        self.lay.addLayout(self.left)
        self.init_menubar()
        self.init_instrs()
        self.init_out()
        self.init_regs()

        center = QWidget()
        center.setLayout(self.lay)
        self.setCentralWidget(center)
        self.showMaximized()

    def init_regs(self):
        self.reg_box = QGridLayout()
        self.regs = {}
        i = 0
        for r in REGS:
            self.regs[r] = QLineEdit()
            self.reg_box.addWidget(QLabel(r), i, 0)
            self.reg_box.addWidget(self.regs[r], i, 1)
            i += 1
        self.lay.addLayout(self.reg_box)

    def init_instrs(self):
        self.instrs = QTextEdit()
        self.instrs.setLineWrapMode(QTextEdit.NoWrap)
        self.instrs.setReadOnly(True)
        self.left.addWidget(self.instrs)

    def init_menubar(self):
        bar = self.menuBar()

        file_ = bar.addMenu("File")
        open_ = QAction("Open", self)
        open_.triggered.connect(self.open_file)
        file_.addAction(open_)

        tools = bar.addMenu("Tools")
        help_ = bar.addMenu("Help")

        run = bar.addMenu("Run")
        start = QAction("Start", self)
        start.triggered.connect(self.start)
        run.addAction(start)

    def init_out(self):
        self.out = QTextEdit()
        self.left.addWidget(self.out)

    def open_file(self):
        try:
            filename = QFileDialog.getOpenFileName(self, 'Open', '.', options=QFileDialog.DontUseNativeDialog)
        except:
            print('failed')
            return

        if not filename or len(filename[0]) == 0:
            return

        lexer = MipsLexer()
        data, lines = preprocess(filename[0], lexer)
        parser = MipsParser(lines)

        r1 = lexer.tokenize(data)
        result = parser.parse(r1)
        self.intr = Interpreter(result, [])
        self.update_screen()
        self.intr.step.connect(self.update_screen)

    def start(self):
        if self.intr:
            x = Thread(target=self.intr.interpret, daemon=True)
            x.start()

    def update_screen(self):
        self.fill_reg()
        self.fill_instrs()
            #self.fill_mem()

    def fill_reg(self):
        for r in REGS:
            self.regs[r].setText(str(self.intr.reg[r]))

    def fill_instrs(self):
        pc = self.intr.reg['pc']
        if len(self.instrs.toPlainText()) > 0:
            # fmt = QTextCharFormat()
            cur = self.instrs.textCursor()

            # cur.select(QTextCursor.Document)
            # cur.setCharFormat(fmt)

            cur = self.instrs.textCursor()
            block = self.instrs.document().findBlockByLineNumber((pc - settings['initial_pc'] - 4) // 4)
            cur.setPosition(block.position())
            fmt = QTextCharFormat()
            fmt.setBackground(Qt.cyan)
            cur.select(QTextCursor.LineUnderCursor)
            cur.setCharFormat(fmt)

        else:
            mem = self.intr.mem
            for k in mem.text.keys():
                if type(mem.text[k]) is not str:
                    if mem.text[k].is_from_pseudoinstr:
                        self.instrs.append(f'0x{int(k):08x}\t{mem.text[k].original_text.strip()} ( {mem.text[k].basic_instr()} )')

                    else:
                        self.instrs.append(f'0x{int(k):08x}\t{mem.text[k].original_text.strip()}')


            cur = self.instrs.textCursor()
            block = self.instrs.document().findBlockByLineNumber(0)
            cur.setPosition(block.position())
            fmt = QTextCharFormat()
            fmt.setBackground(Qt.cyan)
            cur.select(QTextCursor.LineUnderCursor)
            cur.setCharFormat(fmt)
            self.instrs.verticalScrollBar().setValue(self.instrs.verticalScrollBar().minimum())

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow(app)
    app.exec_()

