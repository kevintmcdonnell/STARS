from PySide2.QtWidgets import QMainWindow, QAction, QApplication, QFileDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QWidget, QLineEdit, QTextEdit, QFrame, QPushButton
from PySide2.QtCore import Signal, Qt, QSemaphore
from PySide2.QtGui import QFont, QTextCharFormat, QTextCursor

from constants import REGS
from interpreter.interpreter import Interpreter
from preprocess import preprocess
from sbumips import MipsLexer, MipsParser
from settings import settings
from threading import Thread

class MainWindow(QMainWindow):

    def __init__(self, app):
        super().__init__()
        self.app = app

        settings['gui'] = True
        self.console_sem = QSemaphore(1)
        self.mem_sem = QSemaphore(1)
        #settings['debug'] = True
        self.result = None
        self.intr = None
        self.cur_file = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("STARS")
        self.lay = QHBoxLayout()
        self.left = QVBoxLayout()
        self.right = QVBoxLayout()
        self.lay.addLayout(self.left)
        self.lay.addLayout(self.right)
        self.init_menubar()
        self.init_instrs()
        self.init_mem()
        self.init_out()
        self.init_regs()


        center = QWidget()
        center.setLayout(self.lay)
        self.setCentralWidget(center)
        self.showMaximized()

    def init_regs(self):
        self.reg_box = QGridLayout()
        self.reg_box.setSpacing(0)
        self.regs = {}
        i = 0
        for r in REGS:
            self.regs[r] = QLineEdit()
            self.reg_box.addWidget(QLabel(r), i, 0)
            self.reg_box.addWidget(self.regs[r], i, 1)
            i += 1
        self.right.addLayout(self.reg_box)

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

    def init_mem(self):
        grid = QGridLayout()
        grid.setSpacing(0)
        grid.addWidget(QLabel(""), 0, 0)
        grid.addWidget(QLabel("+0"), 0, 1)
        grid.addWidget(QLabel("+4"), 0, 2)
        grid.addWidget(QLabel("+8"), 0, 3)
        grid.addWidget(QLabel("+c"), 0, 4)
        self.mem_right = QPushButton("->")
        self.mem_left = QPushButton("<-")
        grid.addWidget(self.mem_left, 0, 5)
        grid.addWidget(self.mem_right, 0, 6)
        self.addresses = [0] * 16
        self.addresses = self.addresses[:]
        self.mem_vals = []
        self.base_address = settings['data_min']
        count = 0
        for i in range(1, 17):
            for j in range(5):
                q = QLabel("h")
                q.setFrameShape(QFrame.Box)
                q.setFrameShadow(QFrame.Raised)
                q.setLineWidth(2)
                if j == 0:
                    q.setText(f'0x{count:08x}')
                    self.addresses[i-1] = q
                else:
                    self.mem_vals.append(q)
                grid.addWidget(q, i, j)
            count += 16
        self.left.addLayout(grid)


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
        self.intr.console_out.connect(self.update_console)
        self.mem_right.clicked.connect(self.mem_rightclick)
        self.mem_left.clicked.connect(self.mem_leftclick)

    def start(self):
        if self.intr:
            self.out.setPlainText('')
            x = Thread(target=self.intr.interpret, daemon=True)
            x.start()

    def update_screen(self):
        self.fill_reg()
        self.fill_instrs()
        self.fill_mem()

    def fill_reg(self):
        for r in REGS:
            self.regs[r].setText(str(self.intr.reg[r]))

    def fill_instrs(self):
        pc = self.intr.reg['pc']
        if len(self.instrs.toPlainText()) > 0:
            fmt = QTextCharFormat()
            cur = self.instrs.textCursor()
            cur.select(QTextCursor.Document)
            cur.setCharFormat(fmt)
            cur.clearSelection()

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

    def fill_mem(self):
        self.mem_sem.acquire()
        mem = self.intr.mem

        count = self.base_address
        for q in self.mem_vals:
            q.setText(f'0x{mem.getByte(count + 3, signed=False):02x} 0x{mem.getByte(count + 2, signed=False):02x} 0x{mem.getByte(count + 1, signed=False):02x} 0x{mem.getByte(count, signed=False):02x}')
            count += 4
        count = self.base_address
        for a in self.addresses:
            a.setText(f'0x{count:08x}')
            count += 16
        self.mem_sem.release()

    def mem_rightclick(self):
        self.mem_sem.acquire()
        if self.base_address <= settings['data_max'] - 256:
            self.base_address += 256
        self.mem_sem.release()
        self.fill_mem()

    def mem_leftclick(self):
        self.mem_sem.acquire()
        if self.base_address >= settings['data_min'] + 256:
            self.base_address -= 256
        self.mem_sem.release()
        self.fill_mem()

    def update_console(self, s):
        self.console_sem.acquire()
        cur = self.out.textCursor()
        cur.setPosition(QTextCursor.End)
        self.out.insertPlainText(s)
        self.console_sem.release()

    def console_input(self):
        print('enter')

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow(app)
    app.exec_()
