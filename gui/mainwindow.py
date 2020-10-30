from threading import Thread

from PySide2.QtCore import Qt, QSemaphore, QEvent
from PySide2.QtGui import QTextCursor, QGuiApplication, QPalette, QColor, QFont, QKeySequence
from PySide2.QtWidgets import *

from constants import REGS
from interpreter.interpreter import Interpreter
from sbumips import assemble
from settings import settings
from controller import Controller
from gui.vt100 import VT100
'''
Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
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
        self.vt100 = None

        self.app = app

        self.controller = Controller(None, None)

        settings['gui'] = True
        settings['debug'] = True

        self.console_sem = QSemaphore(1)
        self.out_pos = 0
        self.mem_sem = QSemaphore(1)
        # settings['debug'] = True
        self.result = None
        self.intr = None
        self.cur_file = None

        self.rep = 'Hexadecimal'

        self.running = False
        self.run_sem = QSemaphore(1)

        self.filename = None

        self.breakpoints = []

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
        self.lay = QGridLayout()
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
        self.regs = {}
        self.reg_box.setSpacing(0)
        i = 0
        for r in REGS:
            self.regs[r] = QLabel('0x00000000')
            self.regs[r].setFont(QFont("Courier New", 8))
            self.regs[r].setFrameShape(QFrame.Box)
            self.regs[r].setFrameShadow(QFrame.Raised)
            #self.regs[r].setLineWidth(2)
            reg_label = QLabel(r)
            reg_label.setFont(QFont("Courier New", 8))
            self.reg_box.addWidget(reg_label, i, 0)
            self.reg_box.addWidget(self.regs[r], i, 1)
            i += 1
        self.lay.addLayout(self.reg_box, 0, 3, 2, 1)

    def init_instrs(self):
        i = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(i)
        self.instrs = []
        self.pcs = []
        self.checkboxes = []
        self.instr_grid = QGridLayout()
        self.instr_grid.setSpacing(0)

        i.setLayout(self.instr_grid)
        scroll.setMaximumHeight(300)
        self.lay.addWidget(scroll, 0, 0)
        # self.instrs = QTextEdit()
        # self.instrs.setLineWrapMode(QTextEdit.NoWrap)
        # self.instrs.setReadOnly(True)
        # self.left.addWidget(self.instrs)

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
        vt = QAction("MMIO Display", self)
        vt.triggered.connect(self.launch_vt100)
        tools.addAction(vt)

        help_ = bar.addMenu("Help")

        run = bar.addMenu("Run")
        start = QAction("Start", self)
        start.triggered.connect(self.start)
        start_short = QShortcut(QKeySequence(self.tr("F5")), self)
        start_short.activated.connect(lambda: start.trigger())
        run.addAction(start)
        step = QAction("Step", self)
        step.triggered.connect(self.step)
        step_short = QShortcut(QKeySequence(self.tr("F7")), self)
        step_short.activated.connect(lambda: step.trigger())
        run.addAction(step)
        back = QAction("Back", self)
        back.triggered.connect(self.reverse)
        back_short = QShortcut(QKeySequence(self.tr("F8")), self)
        back_short.activated.connect(lambda: back.trigger())
        run.addAction(back)
        pause = QAction('Pause', self)
        pause.triggered.connect(self.pause)
        pause_short = QShortcut(QKeySequence(self.tr("F9")), self)
        pause_short.activated.connect(lambda: pause.trigger())
        run.addAction(pause)

    def init_out(self):
        self.out = QTextEdit()
        self.out.installEventFilter(self)
        self.lay.addWidget(self.out, 2, 0)

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
                    q.setFont(QFont("Courier New"))
                    self.addresses[i - 1] = q
                else:
                    self.mem_vals.append(q)
                grid.addWidget(q, i, j)
            count += 16
        self.lay.addLayout(grid, 1, 0)

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
            self.result = assemble(filename)
            self.intr = Interpreter(self.result, [])
            self.controller.set_interp(self.intr)
            self.instrs = []
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
        if not self.controller.good():
            return
        if not self.running:
            self.set_running(True)
            self.assemble(self.filename)
            self.controller.set_interp(self.intr)
            self.controller.pause(False)
            self.out.setPlainText('')
            self.out_pos = self.out.textCursor().position()
            self.program = Thread(target=self.intr.interpret, daemon=True)
            for b in self.breakpoints:
                self.controller.add_breakpoint(b)
            self.program.start()
        elif not self.controller.cont():
            self.controller.pause(False)

    def pause(self):
        if not self.controller.good():
            return
        if self.controller.cont():
            self.controller.pause(True)

    def step(self):
        if not self.controller.good():
            return
        if not self.running:
            self.set_running(True)
            self.assemble(self.filename)
            self.controller.set_interp(self.intr)
            self.controller.set_pause(True)
            self.out.setPlainText('')
            self.program = Thread(target=self.intr.interpret, daemon=True)
            for b in self.breakpoints:
                self.controller.add_breakpoint(b)
            self.program.start()
        else:
            self.controller.set_pause(True)

    def reverse(self):
        if not self.controller.good() or not self.running:
            return
        else:
            self.controller.reverse()

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
        if not run:
            self.instrs = []
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
                a = self.intr.reg[r]
                if a < 0:
                    a += 2**32
                self.regs[r].setText(f'0x{a:08x}')

    def fill_instrs(self):
        pc = self.intr.reg['pc']
        if len(self.instrs) > 0:
            # fmt = QTextCharFormat()
            # self.prev_instr.setTextFormat(fmt)
            #
            #
            # fmt = QTextCharFormat()
            # fmt.setBackground(Qt.cyan)
            # self.instrs[pc - settings['initial_pc']].setTextFormat(fmt)
            self.prev_instr.setStyleSheet("QLineEdit { background: rgb(255, 255, 255) };")
            self.prev_instr = self.instrs[(pc - 4 - settings['initial_pc']) // 4]
            self.prev_instr.setStyleSheet("QLineEdit { background: rgb(0, 255, 255) };")

        else:
            mem = self.intr.mem
            count = 0
            for k in mem.text.keys():
                if type(mem.text[k]) is not str:
                    i = mem.text[k]
                    check = QCheckBox()
                    check.stateChanged.connect(lambda state, i=i: self.add_breakpoint(('b', str(i.filetag.file_name), str(i.filetag.line_no))) if state == Qt.Checked else self.remove_breakpoint(
                        ('b', str(i.filetag.file_name), str(i.filetag.line_no))))
                    self.checkboxes.append(check)
                    self.instr_grid.addWidget(check, count, 0)
                    if i.is_from_pseudoinstr:
                        q = QLineEdit(f'0x{int(k):08x}\t{i.original_text.strip()} ( {i.basic_instr()} )')
                        q.setReadOnly(True)
                        q.setFont(QFont("Courier New", 10))
                        self.instrs.append(q)
                        self.instr_grid.addWidget(q, count, 1)
                    else:
                        q = QLineEdit(f'0x{int(k):08x}\t{i.original_text.strip()}')
                        q.setFont(QFont("Courier New", 10))
                        q.setReadOnly(True)
                        self.instrs.append(q)
                        self.instr_grid.addWidget(q, count, 1)
                    count += 1
            self.instrs[0].setStyleSheet("QLineEdit { background: rgb(0, 255, 255) };")
            self.prev_instr = self.instrs[0]

    def fill_mem(self):
        self.mem_sem.acquire()
        count = self.base_address
        for q in self.mem_vals:
            if self.rep == "Decimal":
                q.setText(f'{self.controller.get_byte(count + 3):3} {self.controller.get_byte(count + 2):3} {self.controller.get_byte(count + 1):3} {self.controller.get_byte(count):3}')
            elif self.rep == "ASCII":
                q.setText(
                    f'{to_ascii(self.controller.get_byte(count + 3, signed=True)):2} {to_ascii(self.controller.get_byte(count + 2, signed=True)):2} {to_ascii(self.controller.get_byte(count + 1, signed=True)):2} {to_ascii(self.controller.get_byte(count, signed=True)):2}')
            else:
                q.setText(
                    f'0x{self.controller.get_byte(count + 4):02x} 0x{self.controller.get_byte(count + 3):02x} 0x{self.controller.get_byte(count + 2):02x} 0x{self.controller.get_byte(count):02x}')
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
        if self.base_address >= 256:
            self.base_address -= 256
        self.mem_sem.release()
        self.fill_mem()

    def update_console(self, s):
        self.console_sem.acquire()
        cur = self.out.textCursor()
        cur.setPosition(QTextCursor.End)
        self.out.insertPlainText(s)
        self.out_pos = self.out.textCursor().position()
        self.console_sem.release()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and obj is self.out:
            if event.key() == Qt.Key_Return and self.out.hasFocus():
                self.console_sem.acquire()
                cur = self.out.textCursor()
                cur.setPosition(self.out_pos, QTextCursor.KeepAnchor)
                s = cur.selectedText()
                cur.setPosition(QTextCursor.End)
                self.out_pos = self.out.textCursor().position()
                self.console_sem.release()
                self.intr.set_input(s)
        return super().eventFilter(obj, event)

    def add_breakpoint(self, cmd):
        self.controller.add_breakpoint(cmd)
        self.breakpoints.append(cmd)

    def remove_breakpoint(self, cmd):
        self.controller.remove_breakpoint((cmd[1], cmd[2]))
        self.breakpoints.remove(cmd)

    def launch_vt100(self):
        if self.vt100:
            self.vt100.close()
        self.vt100 = VT100(self.controller)

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow(app)
    app.exec_()
