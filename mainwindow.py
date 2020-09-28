from threading import Thread

from PySide2.QtCore import Qt, QSemaphore, QEvent
from PySide2.QtGui import QTextCharFormat, QTextCursor, QGuiApplication, QPalette, QColor
from PySide2.QtWidgets import *

from constants import REGS
from interpreter.interpreter import Interpreter
from preprocess import preprocess
from sbumips import MipsLexer, MipsParser
from settings import settings


def to_ascii(c):
    if c in range(127):
        if c == 0:  # Null terminator
            return "\\0"

        elif c == 9:  # Tab
            return "\\t"

        elif c == 10:  # Newline
            return "\\n"

        elif c >= 32:  # Regular character
            return chr(c)

        else:  # Invalid character
            return '.'

    else:  # Invalid character
        return '.'


class MainWindow(QMainWindow):

    def __init__(self, app):
        super().__init__()
        self.app = app

        settings['gui'] = True
        settings['debug'] = True

        self.console_sem = QSemaphore(1)
        self.mem_sem = QSemaphore(1)
        # settings['debug'] = True
        self.result = None
        self.intr = None
        self.cur_file = None

        self.rep = 'Hexadecimal'

        self.running = False
        self.run_sem = QSemaphore(1)

        self.filename = None

        self.default_theme = QGuiApplication.palette()
        self.dark = False
        self.palette = QPalette()
        self.palette.setColor(QPalette.Window, QColor(25, 25, 25))  # 53 53 53
        self.palette.setColor(QPalette.WindowText, Qt.darkCyan)
        self.palette.setColor(QPalette.Base, QColor(53, 53, 53))  # 25 25 25
        self.palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        self.palette.setColor(QPalette.ToolTipBase, Qt.darkCyan)
        self.palette.setColor(QPalette.ToolTipText, Qt.darkCyan)
        self.palette.setColor(QPalette.Text, Qt.darkCyan)
        self.palette.setColor(QPalette.Button, QColor(53, 53, 53))
        self.palette.setColor(QPalette.ButtonText, Qt.darkCyan)
        self.palette.setColor(QPalette.BrightText, Qt.red)
        self.palette.setColor(QPalette.Link, QColor(42, 130, 218))
        self.palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        self.palette.setColor(QPalette.HighlightedText, Qt.black)

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
        dark_mode = QAction("Dark Mode", self)
        dark_mode.triggered.connect(self.change_theme)
        tools.addAction(dark_mode)

        help_ = bar.addMenu("Help")

        run = bar.addMenu("Run")
        start = QAction("Start", self)
        start.triggered.connect(self.start)
        run.addAction(start)
        step = QAction("Step", self)
        step.triggered.connect(self.step)
        run.addAction(step)
        back = QAction("Back", self)
        back.triggered.connect(self.reverse)
        run.addAction(back)
        pause = QAction('Pause', self)
        pause.triggered.connect(self.pause)
        run.addAction(pause)

    def init_out(self):
        self.out = QTextEdit()
        self.out.installEventFilter(self)
        self.left.addWidget(self.out)

    def init_mem(self):
        grid = QGridLayout()
        self.section_dropdown = QComboBox()
        self.section_dropdown.addItems(['Kernel', '.data', 'stack'])
        self.section_dropdown.currentTextChanged.connect(self.change_section)
        grid.addWidget(self.section_dropdown, 0, 0)
        grid.setSpacing(0)
        grid.addWidget(QLabel("+0"), 0, 1)
        grid.addWidget(QLabel("+4"), 0, 2)
        grid.addWidget(QLabel("+8"), 0, 3)
        grid.addWidget(QLabel("+c"), 0, 4)
        self.mem_right = QPushButton("->")
        self.mem_left = QPushButton("<-")
        self.hdc_dropdown = QComboBox()
        self.hdc_dropdown.addItems(["Hexadecimal", "Decimal", "ASCII"])
        self.hdc_dropdown.currentTextChanged.connect(self.change_rep)
        grid.addWidget(self.mem_left, 0, 5)
        grid.addWidget(self.mem_right, 0, 6)
        grid.addWidget(self.hdc_dropdown, 1, 5, 1, 2)
        self.addresses = [0] * 16
        self.addresses = self.addresses[:]
        self.mem_vals = []
        self.base_address = 0
        count = 0
        for i in range(1, 17):
            for j in range(5):
                q = QLabel("h")
                q.setFrameShape(QFrame.Box)
                q.setFrameShadow(QFrame.Raised)
                q.setLineWidth(2)
                if j == 0:
                    q.setText(f'0x{count:08x}')
                    self.addresses[i - 1] = q
                else:
                    self.mem_vals.append(q)
                grid.addWidget(q, i, j)
            count += 16
        self.left.addLayout(grid)

    def open_file(self):
        try:
            filename = QFileDialog.getOpenFileName(self, 'Open', '.', options=QFileDialog.DontUseNativeDialog)
        except:
            self.out.setPlainText("Could not open file.")
            return

        if not filename or len(filename[0]) == 0:
            return

        self.assemble(filename[0])

    def assemble(self, filename):
        try:
            lexer = MipsLexer()
            data, lines = preprocess(filename, lexer)
            parser = MipsParser(lines)

            r1 = lexer.tokenize(data)
            self.result = parser.parse(r1)
            self.intr = Interpreter(self.result, [])
            self.update_screen()
            self.intr.step.connect(self.update_screen)
            self.intr.console_out.connect(self.update_console)
            self.mem_right.clicked.connect(self.mem_rightclick)
            self.mem_left.clicked.connect(self.mem_leftclick)
            self.intr.end.connect(self.set_running)

            self.setWindowTitle(f'STARS: {filename}')
            self.filename = filename
        except Exception as e:
            print(e)
            if hasattr(e, 'message'):
                self.console_sem.acquire()
                self.out.setPlainText(type(e).__name__ + ": " + e.message)
                self.console_sem.release()

            else:
                self.console_sem.acquire()
                self.out.setPlainText(type(e).__name__ + ": " + str(e))
                self.console_sem.release()

    def change_theme(self):
        if not self.dark:
            self.app.setPalette(self.palette)
            for reg in REGS:
                self.regs[reg].setPalette(self.palette)
        else:
            self.app.setPalette(self.default_theme)
            for reg in REGS:
                self.regs[reg].setPalette(self.default_theme)
        self.dark = not self.dark

    def start(self):
        if not self.intr:
            return
        if not self.running:
            self.set_running(True)
            self.assemble(self.filename)
            self.intr.pause(False)
            self.out.setPlainText('')
            self.program = Thread(target=self.intr.interpret, daemon=True)
            self.program.start()
        elif not self.intr.debug.continueFlag:
            self.intr.pause(False)

    def pause(self):
        if not self.intr:
            return
        if self.intr.debug.continueFlag:
            self.intr.pause(True)

    def step(self):
        if not self.intr:
            return
        if not self.running:
            self.set_running(True)
            self.assemble(self.filename)
            self.intr.pause_lock.set()
            self.out.setPlainText('')
            self.program = Thread(target=self.intr.interpret, daemon=True)
            self.program.start()
        else:
            self.intr.pause_lock.set()

    def reverse(self):
        if not self.intr or not self.running:
            return
        else:
            self.intr.debug.reverse(None, self.intr)

    def change_rep(self, t):
        self.rep = t
        self.update_screen()

    def change_section(self, t):
        if t == 'Kernel':
            self.base_address = 0
        elif t == '.data':
            self.base_address = settings['data_min']
        else:
            self.base_address = settings['initial_$sp']
        self.fill_mem()

    def set_running(self, run):
        self.run_sem.acquire()
        self.running = run
        self.run_sem.release()

    def update_screen(self):
        self.fill_reg()
        self.fill_instrs()
        self.fill_mem()

    def fill_reg(self):
        for r in REGS:
            if self.rep == "Decimal":
                self.regs[r].setText(str(self.intr.reg[r]))
            else:
                self.regs[r].setText(f'0x{self.intr.reg[r]:08x}')

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
            if self.rep == "Decimal":
                q.setText(f'{mem.getByte(count + 3, admin=True):3} {mem.getByte(count + 2, admin=True):3} {mem.getByte(count + 1, admin=True):3} {mem.getByte(count, admin=True):3}')
            elif self.rep == "ASCII":
                q.setText(
                    f'{to_ascii(mem.getByte(count + 3, signed=False, admin=True)):2} {to_ascii(mem.getByte(count + 2, signed=False, admin=True)):2} {to_ascii(mem.getByte(count + 1, signed=False, admin=True)):2} {to_ascii(mem.getByte(count, signed=False, admin=True)):2}')
            else:
                q.setText(
                    f'0x{mem.getByte(count + 3, signed=False, admin=True):02x} 0x{mem.getByte(count + 2, signed=False, admin=True):02x} 0x{mem.getByte(count + 1, signed=False, admin=True):02x} 0x{mem.getByte(count, signed=False, admin=True):02x}')
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

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and obj is self.out:
            print(event.key())
            if event.key() in range(256):
                print(f'\t{chr(event.key())}')
            if event.key() == Qt.Key_Return and self.out.hasFocus():
                print('Enter pressed')
        return super().eventFilter(obj, event)


if __name__ == "__main__":
    app = QApplication()
    window = MainWindow(app)
    app.exec_()
