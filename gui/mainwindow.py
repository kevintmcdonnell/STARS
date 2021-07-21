import os
import sys
from threading import Thread

sys.path.append(os.getcwd())  # must be ran in sbumips directory (this is bc PYTHONPATH is weird in terminal)
from constants import REGS, F_REGS, MENU_BAR
from interpreter.interpreter import Interpreter
from sbumips import assemble
from settings import settings
from controller import Controller
from gui.vt100 import VT100
from gui.textedit import TextEdit
from gui.syntaxhighlighter import Highlighter
from gui.widgetfactory import *

from PySide2.QtCore import Qt, QSemaphore, QEvent, Signal, QFile, QStringListModel
from PySide2.QtGui import QTextCursor, QGuiApplication, QPalette, QColor, QFont, QKeySequence, QCursor, QBrush
from PySide2.QtWidgets import *

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
    changed_interp = Signal()

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
        self.result = None
        self.intr = None
        self.cur_file = None

        self.rep = 'Hexadecimal'

        self.running = False
        self.run_sem = QSemaphore(1)

        self.default_theme = QGuiApplication.palette()
        self.dark = False
        self.palette = QPalette()
        self.palette.setColor(QPalette.Window, QColor(25, 25, 25))  # 53 53 53
        self.palette.setColor(QPalette.WindowText, Qt.white)
        self.palette.setColor(QPalette.Base, QColor(53, 53, 53))  # 25 25 25
        self.palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        self.palette.setColor(QPalette.ToolTipBase, Qt.white)
        self.palette.setColor(QPalette.ToolTipText, Qt.white)
        self.palette.setColor(QPalette.Text, Qt.white)
        self.palette.setColor(QPalette.Button, QColor(53, 53, 53))
        self.palette.setColor(QPalette.ButtonText, Qt.white)
        self.palette.setColor(QPalette.BrightText, Qt.red)
        self.palette.setColor(QPalette.Link, QColor(42, 130, 218))
        self.palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        self.palette.setColor(QPalette.HighlightedText, Qt.black)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("STARS")
        self.lay = QGridLayout()
        self.lay.setSpacing(5)
        self.init_menubar()
        self.init_instrs()
        self.init_mem()
        self.init_out()
        self.init_regs()
        self.init_pa()
        self.init_cop_flags()
        self.add_edit()
        center = QWidget()
        center.setLayout(self.lay)
        self.setCentralWidget(center)
        self.showMaximized()
        self.init_splitters()

    def init_regs(self):
        self.regs = {}
        self.reg_box = QTabWidget()
        reg_box = create_table(len(REGS), 2, ["Name", "Value"], stretch_last=True)
        reg_box.resizeRowsToContents()
        for i, r in enumerate(REGS):
            self.regs[r] = QTableWidgetItem('0x00000000')
            self.regs[r].setFont(QFont("Courier New", 8))
            self.regs[r].setTextAlignment(int(Qt.AlignRight))
            reg_label = QTableWidgetItem(r)
            reg_label.setFont(QFont("Courier New", 8))
            reg_box.setItem(i, 0, reg_label)
            reg_box.setItem(i, 1, self.regs[r])
            
        freg_box = create_table(len(F_REGS), 2, ["Name", "Value"], stretch_last=True) 
        freg_box.resizeRowsToContents()
        for i, r in enumerate(F_REGS):
            self.regs[r] = QTableWidgetItem('0x00000000')
            self.regs[r].setFont(QFont("Courier New", 8))
            self.regs[r].setTextAlignment(int(Qt.AlignRight))
            reg_label = QTableWidgetItem(r)
            reg_label.setFont(QFont("Courier New", 8))
            freg_box.setItem(i, 0, reg_label)
            freg_box.setItem(i, 1, self.regs[r])
        self.reg_box.addTab(reg_box, "Registers")
        self.reg_box.addTab(freg_box, "Coproc 1")
        self.reg_box.tabBar().setDocumentMode(True)


    def init_cop_flags(self):
        flag_box = QGridLayout()
        flag_box.setSpacing(0)
        self.flags = []
        count = 0
        for i in range(1, 5):
            c1 = QCheckBox(f'{count}')
            self.flags.append(c1)
            count += 1
            c2 = QCheckBox(f'{count}')
            count += 1
            self.flags.append(c2)
            flag_box.addWidget(c1, i, 0)
            flag_box.addWidget(c2, i, 1)
        flag_box.addWidget(QLabel('Coproc 1 Flags:'), 0, 0)
        # self.lay.addLayout(flag_box, 3, 3)

    def init_instrs(self):
        self.instrs = []
        self.pcs = []
        self.instr_grid = create_table(0, 4, ["Bkpt", f"{'Address': ^14}", f"{'Instruction': ^40}", "Source"], stretch_last=True)
        self.instr_grid.resizeColumnsToContents()

    def add_edit(self):
        self.files = {} # filename -> (dirty: bool, path: str)
        self.new_files = set()
        self.highlighter = {}

        self.count = 0
        self.len = 0
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        nt = QPushButton('+')
        nt.clicked.connect(self.new_tab)
        self.tabs.setCornerWidget(nt)


        text_edit = TextEdit()
        self.comp = QCompleter()
        self.comp.setModel(self.modelFromFile(r"gui/wordslist.txt", self.comp))
        self.comp.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.comp.setCaseSensitivity(Qt.CaseInsensitive)
        self.comp.setWrapAround(False)
        text_edit.setCompleter(self.comp)


    def modelFromFile(self, filename, comp):
        f = QFile(filename)
        if not f.open(QFile.ReadOnly):
            return QStringListModel(comp)

        QGuiApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        words = []
        while not f.atEnd():
            line = f.readLine()
            if len(line) > 0:
                s = str(line.trimmed(), encoding='ascii')
                words.append(s)

        QGuiApplication.restoreOverrideCursor()

        return QStringListModel(words, comp)

    def init_menubar(self):
        bar = self.menuBar()
        self.menu_items = {}

        for tabs, values in MENU_BAR.items():
            tab = bar.addMenu(tabs)
            if tabs == 'Settings':
                tab.triggered.connect(lambda selection: self.controller.setSetting(selection.data(), selection.isChecked()))
            for option, controls in values.items():
                action = QAction(f"&{option}", self) if 'Shortcut' in controls else QAction(option, self)
                if 'Checkbox' in controls:
                    action.setCheckable(True)
                    action.setData(controls['Checkbox'])
                    action.setChecked(settings[controls['Checkbox']])
                if 'Action' in controls:
                    action.triggered.connect(eval(controls['Action']))
                if 'Shortcut' in controls:
                    action.setShortcut(controls['Shortcut'])
                if 'Tag' in controls:
                    self.menu_items[controls['Tag']] = action
                if 'Start' in controls:
                    action.setEnabled(controls['Start'])
                tab.addAction(action)

        self.instr_count = QLabel("Instruction Count: 0\t\t")
        bar.setCornerWidget(self.instr_count)

    def init_out(self):
        self.out = QTextEdit()
        self.out.setReadOnly(True)
        self.out.installEventFilter(self)
        clear_button = QPushButton("Clear")
        clear_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        clear_button.pressed.connect(lambda: self.update_console(clear=True))
        grid = QGridLayout()
        grid.setSpacing(0)
        self.out_section = QWidget()
        grid.addWidget(clear_button, 0, 0, 1, 1)
        grid.addWidget(self.out, 0, 1, 1, 49)
        self.out_section.setLayout(grid)

    def init_mem(self):
        grid = QGridLayout()
        grid.setSpacing(5)
        self.section_dropdown = QComboBox()
        self.section_dropdown.addItems(['Kernel', '.data', 'stack', 'MMIO'])
        self.section_dropdown.currentTextChanged.connect(self.change_section)
        self.mem_right = QPushButton("🡣")
        self.mem_right.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.mem_right.setMaximumWidth(25)
        self.mem_left = QPushButton("🡡")
        self.mem_left.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.mem_left.setMaximumWidth(25)
        self.hdc_dropdown = QComboBox()
        self.hdc_dropdown.addItems(["Hexadecimal", "Decimal", "ASCII"])
        self.hdc_dropdown.currentTextChanged.connect(self.change_rep)
        grid.addWidget(self.mem_left, 1, 5, 8, 1)
        grid.addWidget(self.mem_right, 9, 5, 8, 1)
        grid.addWidget(self.section_dropdown, 1, 6, 1, 1)
        grid.addWidget(self.hdc_dropdown, 1, 7, 1, 1)
        self.addresses = [0] * 16
        self.addresses = self.addresses[:]
        self.mem_vals = []
        self.base_address = 0
        table = create_table(16, 5, ["Address", "+0", "+4", "+8", "+c"])
        count = 0
        for i in range(16):
            for j in range(5):
                q = QTableWidgetItem(" ")
                if j == 0:
                    q.setText(f'0x{count:08x}')
                    q.setFont(QFont("Courier New"))
                    self.addresses[i - 1] = q
                else:
                    self.mem_vals.append(q)
                table.setItem(i, j, q)
            count += 16
        grid.addWidget(table, 1, 0, 16, 5)
        self.labels = create_table(0, 3, ['', 'Label', 'Address'])
        self.labels.setSortingEnabled(True)
        grid.addWidget(self.labels, 2, 6, 15, 2)
        self.mem_grid = QWidget()
        self.mem_grid.setLayout(grid)

    def init_pa(self):
        self.pa = QLineEdit()
        pa = QHBoxLayout()
        label = QLabel('Program Arguments:')
        pa.addWidget(label)
        pa.addWidget(self.pa)
        self.pa_lay = QWidget()
        self.pa_lay.setLayout(pa)

    def init_splitters(self): 
        instruction_pa = QSplitter()
        instruction_pa.setOrientation(Qt.Vertical)
        instruction_pa.addWidget(self.pa_lay)
        instruction_pa.addWidget(self.instr_grid)
        instruction_pa.setStretchFactor(0, 1)
        instruction_pa.setStretchFactor(1, 9)

        editor_instruction_horizontal = QSplitter()
        editor_instruction_horizontal.addWidget(self.tabs)
        editor_instruction_horizontal.addWidget(instruction_pa)
        largeWidth = QGuiApplication.primaryScreen().size().width()
        editor_instruction_horizontal.setSizes([largeWidth, largeWidth]) # 50|50

        left_vertical = QSplitter()
        left_vertical.setOrientation(Qt.Vertical)
        left_vertical.addWidget(editor_instruction_horizontal)
        left_vertical.addWidget(self.mem_grid)
        left_vertical.addWidget(self.out_section)
        left_vertical.setStretchFactor(0, 10)
        left_vertical.setStretchFactor(1, 4)
        left_vertical.setStretchFactor(2, 2)

        all_horizontal = QSplitter()
        all_horizontal.addWidget(left_vertical)
        all_horizontal.addWidget(self.reg_box)
        all_horizontal.setStretchFactor(0, 3)
        all_horizontal.setStretchFactor(1, 0)

        self.lay.addWidget(all_horizontal, 0, 0)

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
                if not self.files[key]:
                    return
                f = open(key, 'w+')

                f.write(to_write)
                f.close()
                self.files[key] = False
                n = key.split('/')[-1]
                self.tabs.setTabText(ind, n)

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
            self.update_console(f'Could not open file\n')
            return

        if not filename or len(filename[0]) == 0:
            return

        s = []
        with open(filename[0]) as f:
            s = f.readlines()
        wid = TextEdit(name=filename[0])
        wid.textChanged.connect(self.update_dirty)
        wid.setCompleter(self.comp)
        wid.setPlainText(''.join(s))
        n = filename[0].split('/')[-1]
        if not filename[0] in self.files:
            self.files[filename[0]] = False
            self.new_tab(wid=wid, name=n)


    def assemble(self):
        if self.tabs.currentWidget() is None:
            return
        filename = self.tabs.currentWidget().name
        try:
            if self.running:
                self.intr.end.emit(False)
            for i in range(self.len):
                self.save_file(wid=self.tabs.widget(i), ind=i)
            self.result = assemble(filename)
            self.intr = Interpreter(self.result, self.pa.text().split())
            self.controller.set_interp(self.intr)
            self.instrs = []
            self.update_screen(self.intr.reg['pc'])
            self.fill_labels()
            self.intr.step.connect(self.update_screen)
            self.intr.console_out.connect(self.update_console)
            self.mem_right.clicked.connect(self.mem_rightclick)
            self.mem_left.clicked.connect(self.mem_leftclick)
            self.intr.end.connect(self.set_running)
            self.setWindowTitle(f'STARS')
            self.update_button_status(start=True, step=True, backstep=True, pause=True)

        except Exception as e:
            if hasattr(e, 'message'):
                self.update_console(type(e).__name__ + ": " + e.message)
            else:
                self.update_console(type(e).__name__ + ": " + str(e))

    def change_theme(self):
        if not self.dark:
            self.app.setPalette(self.palette)
            # for reg in REGS:
            #     self.regs[reg].setPalette(self.palette)
        else:
            self.app.setPalette(self.default_theme)
            # for reg in REGS:
            #     self.regs[reg].setPalette(self.default_theme)
        self.dark = not self.dark

    def start(self):
        if not self.controller.good():
            return
        if not self.running:
            self.set_running(True)
            self.controller.set_interp(self.intr)
            self.changed_interp.emit()
            self.controller.pause(False)
            self.out_pos = self.out.textCursor().position()
            self.program = Thread(target=self.intr.interpret, daemon=True)
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
            self.controller.set_interp(self.intr)
            self.controller.set_pause(True)
            self.program = Thread(target=self.intr.interpret, daemon=True)
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
        if self.controller.good():
            self.update_screen(self.intr.reg['pc'])

    def change_section(self, t):
        if t == 'Kernel':
            self.base_address = 0
        elif t == '.data':
            self.base_address = settings['data_min']
        elif t == 'MMIO':
            self.base_address = 0xffff0000
        else:
            self.base_address = settings['initial_$sp'] - 0xc
            if self.base_address % 256 != 0:
                self.base_address -= self.base_address % 256
        if self.controller.good():
            self.fill_mem()

    def set_running(self, run):
        self.run_sem.acquire()
        self.running = run
        if not run:
            self.instrs = []
            self.update_console("\n-- program is finished running --\n\n")
            self.update_button_status(start=False, step=False, pause=False)
        self.run_sem.release()

    def update_screen(self, pc):
        self.fill_reg()
        self.fill_instrs(pc)
        self.fill_mem()
        self.fill_flags()
        self.instr_count.setText(f'Instruction Count: {self.controller.get_instr_count()}\t\t')

    def fill_labels(self):
        labels = self.controller.get_labels()
        self.labels.setRowCount(len(labels))
        for i, l in enumerate(labels):
            q = QPushButton(f'{l}: 0x{labels[l]:08x}')
            q.clicked.connect(lambda : self.mem_move_to(labels[l]))
            self.labels.setCellWidget(i, 0, q)
            self.labels.setItem(i, 1, QTableWidgetItem(f'{l}'))
            self.labels.setItem(i, 2, QTableWidgetItem(f'0x{labels[l]:08x}'))

    def mem_move_to(self, addr):
        self.mem_sem.acquire()

        if addr % 256 == 0:
            self.base_address = addr

        else:
            addr -= (addr % 256)
            self.base_address = addr

        self.mem_sem.release()

        self.section_dropdown.setCurrentIndex(0)
        if addr >= settings['data_min']:
            self.section_dropdown.setCurrentIndex(1)
        if addr >= 0xffff0000:
            self.section_dropdown.setCurrentIndex(2)

        self.fill_mem()

    def fill_flags(self):
        for i in range(len(self.intr.condition_flags)):
            if self.intr.condition_flags[i]:
                self.flags[i].setCheckState(Qt.Checked)
            else:
                self.flags[i].setCheckState(Qt.Unchecked)

    def fill_reg(self):
        for r in self.regs.keys():
            if r in REGS:
                if self.rep == "Decimal":
                    self.regs[r].setText(str(self.intr.reg[r]))
                else:
                    a = self.intr.reg[r]
                    if a < 0:
                        a += 2 ** 32
                    self.regs[r].setText(f'0x{a:08x}')
            else:
                if self.rep == "Decimal":
                    self.regs[r].setText(f'{self.intr.f_reg[r]:8f}')
                else:
                    self.regs[r].setText(f'0x{self.controller.get_reg_word(r):08x}')

    def fill_instrs(self, pc):
        # pc = self.intr.reg['pc']
        if len(self.instrs) > 0:
            prev_ind = (pc - settings['initial_pc']) // 4
            for section in self.prev_instr:
                section.setBackground(self.instr_grid.item(prev_ind, 1).background())
            if prev_ind < len(self.instrs):
                self.prev_instr = self.instrs[prev_ind]
            for section in self.prev_instr:
                section.setBackground(QBrush(Qt.cyan))
        else:
            mem = self.intr.mem
            self.instr_grid.setRowCount(len([k for k,j in mem.text.items() if type(j) is not str]))
            for count, (k, i) in enumerate(mem.text.items()):
                if type(i) is not str:
                    cell, check = create_breakpoint()
                    check.stateChanged.connect(lambda state, i=i: self.add_breakpoint(('b', str(i.filetag.file_name)[1:-1], str(i.filetag.line_no))) if state == Qt.Checked else self.remove_breakpoint(
                        ('b', str(i.filetag.file_name)[1:-1], str(i.filetag.line_no))))
                    self.instr_grid.setCellWidget(count, 0, cell)
                    
                    values = [f"0x{int(k):08x}", 
                                f"{i.basic_instr()}", 
                                f"{i.filetag.line_no}: {i.original_text}"]
                    row = create_instruction(values, self.instr_grid, count)
                    self.instrs.append(row)
            for section in self.instrs[0]:
                section.setBackground(QBrush(Qt.cyan))
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
                    f'0x{self.controller.get_byte(count + 3):02x} 0x{self.controller.get_byte(count + 2):02x} 0x{self.controller.get_byte(count + 1):02x} 0x{self.controller.get_byte(count):02x}')
            count += 4
        count = self.base_address
        for a in self.addresses:
            a.setText(f'0x{count:08x}')
            count += 16
        self.mem_sem.release()

    def mem_rightclick(self):
        if not self.controller.good():
            return
        self.mem_sem.acquire()
        if self.base_address <= settings['data_max'] - 256:
            self.base_address += 256
        self.mem_sem.release()
        self.fill_mem()

    def mem_leftclick(self):
        if not self.controller.good():
            return
        self.mem_sem.acquire()
        if self.base_address >= 256:
            self.base_address -= 256
        self.mem_sem.release()
        self.fill_mem()

    def update_console(self, s="", clear=False):
        self.console_sem.acquire()
        if clear:
            self.out.setPlainText(s)
        else:
            self.out.insertPlainText(s)
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

    def remove_breakpoint(self, cmd):
        self.controller.remove_breakpoint((f'"{cmd[1]}"', cmd[2]))

    def launch_vt100(self):
        if self.vt100:
            self.vt100.close()
        self.vt100 = VT100(self.controller, self.changed_interp)

    def close_tab(self, i):
        if self.tabs.currentIndex() == i:
            self.update_button_status(start=False, step=False, backstep=False, pause=False)
        if self.tabs.widget(i).name in self.files:
            self.files.pop(self.tabs.widget(i).name)
        self.tabs.removeTab(i)
        self.len -= 1
        if self.len == 0:
            self.update_button_status(assemble=False, start=False, step=False, backstep=False, pause=False)

    def new_tab(self, wid=None, name=''):
        self.count += 1
        self.len += 1
        if len(name) == 0:
            name = f'main{"" if self.count == 1 else self.count-1}.asm'
        if not wid:
            wid = TextEdit(name=name)
            wid.setCompleter(self.comp)
            wid.textChanged.connect(self.update_dirty)
        self.tabs.addTab(wid, name)
        self.tabs.setCurrentWidget(wid)
        self.update_button_status(assemble=True)
        self.highlighter[name] = Highlighter(wid.document())

    def update_dirty(self):
        w = self.tabs.currentWidget()
        i = self.tabs.currentIndex()
        if w is not None and (w.name not in self.files or not self.files[w.name]):
            self.tabs.setTabText(i, f'{self.tabs.tabText(i)} *')
        if w:
            self.files[w.name] = True

    def update_button_status(self, **button_status):
        for tag, status in button_status.items():
            self.menu_items[tag].setEnabled(status)

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow(app)
    app.exec_()