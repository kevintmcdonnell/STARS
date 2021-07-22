import os
import sys
from threading import Thread

sys.path.append(os.getcwd())  # must be ran in sbumips directory (this is bc PYTHONPATH is weird in terminal)
from constants import *
from interpreter.interpreter import Interpreter
from sbumips import assemble
from settings import settings
from controller import Controller
from gui.vt100 import VT100
from gui.textedit import TextEdit
from gui.syntaxhighlighter import Highlighter
from gui.widgetfactory import *

from PySide2.QtCore import Qt, QSemaphore, QEvent, Signal, QFile, QStringListModel
from PySide2.QtGui import QTextCursor, QGuiApplication, QPalette, QColor, QKeySequence, QCursor, QBrush
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
        self.mem_sem = QSemaphore(1)
        self.result = None
        self.intr = None

        self.rep = MEMORY_REPR_DEFAULT

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
        self.setWindowTitle(WINDOW_TITLE)
        self.init_menubar()
        self.init_instrs()
        self.init_mem()
        self.init_out()
        self.init_regs()
        self.init_pa()
        self.add_edit()
        self.init_splitters()
        self.showMaximized()

    def init_regs(self):
        self.regs = {}
        self.flags = []
        self.reg_box = QTabWidget()
        self.reg_box.tabBar().setDocumentMode(True)
        for name, register_set in {"Registers": REGS, "Coproc 1": F_REGS}.items():
            box = create_table(len(register_set), len(REGISTER_HEADER), REGISTER_HEADER, stretch_last=True)
            box.resizeRowsToContents()
            for i, r in enumerate(register_set):
                self.regs[r] = create_cell(WORD_HEX_FORMAT.format(settings.get(f"initial_{r}", 0)))
                self.regs[r].setTextAlignment(int(Qt.AlignRight))
                label = create_cell(r)
                box.setItem(i, 0, label)
                box.setItem(i, 1, self.regs[r])
            if name == "Coproc 1": # add coproc flags
                flags = create_table(4, len(COPROC_FLAGS_HEADER), COPROC_FLAGS_HEADER)
                for count in range(8):
                    cell, check = create_breakpoint(f"{count}")
                    self.flags.append(check)
                    flags.setCellWidget(count/2, count%2, cell)
                box = create_splitter(orientation=Qt.Vertical,
                    widgets=[box, flags], stretch_factors=[20])
            self.reg_box.addTab(box, name)

    def init_instrs(self):
        self.instrs = []
        self.pcs = []
        self.instr_grid = create_table(0, len(INSTR_HEADER), INSTR_HEADER, stretch_last=True)
        self.instr_grid.resizeColumnsToContents()

    def add_edit(self):
        self.files = {} # filename -> (dirty: bool, path: str)
        self.file_count = 0 # number of tabs

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setCornerWidget(create_button('+', self.new_tab))

        # initialize autocomplete
        self.comp = QCompleter()
        self.comp.setModel(self.modelFromFile(WORDLIST_PATH, self.comp))
        self.comp.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.comp.setCaseSensitivity(Qt.CaseInsensitive)
        self.comp.setWrapAround(False)

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
                action = QAction(option, self)
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

        self.instr_count = QLabel(INSTRUCTION_COUNT.format(0))
        bar.setCornerWidget(self.instr_count)

    def init_out(self):
        self.out = QTextEdit()
        self.out.setReadOnly(True)
        clear_button = create_button("Clear", lambda: self.update_console(clear=True), (QSizePolicy.Minimum, QSizePolicy.Expanding))
        grid = create_box_layout(direction=QBoxLayout.LeftToRight, sections=[clear_button, self.out])
        grid.setSpacing(0)
        self.out_section = create_widget(layout=grid)

    def init_mem(self):
        # initialize memory table and left/right buttons
        self.mem_right = create_button("🡣", self.mem_rightclick, (QSizePolicy.Preferred, QSizePolicy.Expanding), maximum_width=25)
        self.mem_left = create_button("🡡", self.mem_leftclick, (QSizePolicy.Preferred, QSizePolicy.Expanding), maximum_width=25)
        
        self.base_address = settings['data_min']
        table = create_table(MEMORY_ROW_COUNT, MEMORY_COLUMN_COUNT+1, MEMORY_TABLE_HEADER)
        self.addresses = [create_cell(WORD_HEX_FORMAT.format(address)) for address in 
                                range(self.base_address, self.base_address+MEMORY_SIZE, MEMORY_COLUMN_COUNT*MEMORY_WIDTH)]
        for i, cell in enumerate(self.addresses):
            table.setItem(i, 0, cell)
        self.mem_vals = [create_cell() for i in range(MEMORY_ROW_COUNT*MEMORY_COLUMN_COUNT)]
        for i, cell in enumerate(self.mem_vals):
            table.setItem(i/MEMORY_COLUMN_COUNT, (i%MEMORY_COLUMN_COUNT)+1, cell)

        arrow_grid = create_box_layout(direction=QBoxLayout.TopToBottom,
            sections=[self.mem_left, self.mem_right])
        memory_grid = create_box_layout(direction=QBoxLayout.LeftToRight,
            sections=[table, arrow_grid])

        # Initialize dropdowns and labels table
        self.section_dropdown = create_dropdown(MEMORY_SECTION, self.change_section)
        self.section_dropdown.setCurrentIndex(1)
        self.hdc_dropdown = create_dropdown(MEMORY_REPR.keys(), self.change_rep)
        self.labels = create_table(0, len(LABEL_HEADER), LABEL_HEADER)
        self.labels.setSortingEnabled(True)

        dropdown_grid = create_box_layout(direction=QBoxLayout.LeftToRight,
            sections=[self.section_dropdown, self.hdc_dropdown])
        right_area = create_splitter(orientation=Qt.Vertical,
            widgets=[create_widget(layout=dropdown_grid), self.labels])

        # Splitter for the memory area and dropdown/labels area
        self.mem_grid = create_splitter(
            widgets=[create_widget(layout=memory_grid), right_area],
            stretch_factors=[2, 1])

    def init_pa(self):
        self.pa = QLineEdit()
        layout = create_box_layout(direction=QBoxLayout.LeftToRight,
            sections=[QLabel('Program Arguments:'), self.pa])
        self.pa_lay = create_widget(layout=layout)

    def init_splitters(self): 
        largeWidth = QGuiApplication.primaryScreen().size().width()
        instruction_pa = create_splitter(orientation=Qt.Vertical, 
            widgets=[self.pa_lay, self.instr_grid], stretch_factors=[1, 9])
        editor_instruction_horizontal = create_splitter(
            widgets=[self.tabs, instruction_pa], sizes=[largeWidth, largeWidth])
        left_vertical = create_splitter(orientation=Qt.Vertical,
            widgets=[editor_instruction_horizontal, self.mem_grid, self.out_section],
            stretch_factors=[10, 4, 2])
        all_horizontal = create_splitter(
            widgets=[left_vertical, self.reg_box], stretch_factors=[3, 0])
        all_horizontal.setContentsMargins(10,20,10,10)

        self.setCentralWidget(all_horizontal)

    def save_file(self, wid: TextEdit=None, ind: int=None):
        if wid is None:
            wid = self.tabs.currentWidget()
        if ind is None:
            ind = self.tabs.currentIndex()
        if wid.is_new() and self.files.get(wid.name, False):
            filename, _ = QFileDialog.getSaveFileName(self, 'Save', f'{wid.name}', options=QFileDialog.DontUseNativeDialog)
            if not filename:
                return
            value = self.files.pop(wid.name)
            wid.name = filename[0]
            wid.set_new(False)
            self.files[wid.name] = value

        if self.files.get(wid.name, False):
            with open(wid.name, 'w+') as f:
                f.write(wid.toPlainText())
            self.files[wid.name] = False
            self.tabs.setTabText(ind, wid.getFilename())

    def open_file(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(self, 'Open', '', options=QFileDialog.DontUseNativeDialog)
            if not filename:
                return
            if filename not in self.files:
                with open(filename) as f:
                    wid = TextEdit(name=filename, text=f.read(), completer=self.comp, textChanged=self.update_dirty)
                self.new_tab(wid=wid)
        except:
            self.update_console(OPEN_FILE_FAILED)
            return

    def assemble(self):
        if self.tabs.currentWidget() is None:
            return
        try:
            if self.running:
                self.intr.end.emit(False)
            for i in range(self.file_count):
                self.save_file(wid=self.tabs.widget(i), ind=i)
            self.result = assemble(self.tabs.currentWidget().name)
            self.intr = Interpreter(self.result, self.pa.text().split())
            self.controller.set_interp(self.intr)
            self.instrs = []
            self.update_screen(self.intr.reg['pc'])
            self.fill_labels()
            self.intr.step.connect(self.update_screen)
            self.intr.console_out.connect(self.update_console)
            self.intr.user_input.connect(self.get_input)
            self.intr.end.connect(self.set_running)
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
            self.base_address = settings['mmio_base']
        else:
            self.base_address = (settings['initial_$sp'] - 0xc) & ~(MEMORY_SIZE-1) # multiple of MEMORY_SIZE
        self.fill_mem()

    def set_running(self, run):
        self.run_sem.acquire()
        self.running = run
        if not run:
            self.instrs = []
            self.update_console(PROGRAM_FINISHED)
            self.update_button_status(start=False, step=False, pause=False)
        self.run_sem.release()

    def update_screen(self, pc):
        self.fill_reg()
        self.fill_instrs(pc)
        self.fill_mem()
        self.fill_flags()
        self.instr_count.setText(INSTRUCTION_COUNT.format(self.controller.get_instr_count()))

    def fill_labels(self):
        labels = self.controller.get_labels()
        self.labels.setRowCount(len(labels))
        for i, (l, addr) in enumerate(labels.items()):
            q = create_button(f'{l}: {WORD_HEX_FORMAT.format(addr)}', 
                    lambda state=None, addr=addr: self.mem_move_to(addr))
            self.labels.setCellWidget(i, 0, q)
            self.labels.setItem(i, 1, QTableWidgetItem(f'{l}'))
            self.labels.setItem(i, 2, QTableWidgetItem(WORD_HEX_FORMAT.format(addr)))

    def mem_move_to(self, addr):
        self.mem_sem.acquire()
        self.base_address = addr & ~(MEMORY_SIZE-1) # 0x100-1 -> 0xff (multiple of MEMORY_SIZE)
        self.mem_sem.release()
        self.section_dropdown.setCurrentIndex(0)
        if addr >= settings['data_min']:
            self.section_dropdown.setCurrentIndex(1)
        if addr >= settings['mmio_base']:
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
                    self.regs[r].setText(WORD_HEX_FORMAT.format(a))
            else:
                if self.rep == "Decimal":
                    self.regs[r].setText(f'{self.intr.f_reg[r]:8f}')
                else:
                    self.regs[r].setText(WORD_HEX_FORMAT.format(self.controller.get_reg_word(r)))

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
                    
                    values = [WORD_HEX_FORMAT.format(int(k)), 
                                f"{i.basic_instr()}", 
                                f"{i.filetag.line_no}: {i.original_text}"]
                    row = create_instruction(values, self.instr_grid, count)
                    self.instrs.append(row)
            for section in self.instrs[0]:
                section.setBackground(QBrush(Qt.cyan))
            self.prev_instr = self.instrs[0]

    def fill_mem(self):
        self.mem_sem.acquire()
        if self.controller.good():
            for q, count in zip(self.mem_vals, range(self.base_address, self.base_address+MEMORY_SIZE, MEMORY_WIDTH)):
                memory_format = MEMORY_REPR[self.rep]
                signed = True if self.rep == "ASCII" else False
                offsets = range(MEMORY_WIDTH)[::-1] # [3,2,1,0]
                byte_value = [self.controller.get_byte(count+i, signed=signed) for i in offsets]
                if self.rep == "ASCII":
                    byte_value = [to_ascii(value) for value in byte_value]
                text = " ".join([memory_format.format(value) for value in byte_value])
                q.setText(text)
        for a, count in zip(self.addresses, range(self.base_address, self.base_address+MEMORY_SIZE, MEMORY_COLUMN_COUNT*MEMORY_WIDTH)):
            text = f'{count}' if self.rep == "Decimal" else WORD_HEX_FORMAT.format(count)
            a.setText(text)
        self.mem_sem.release()

    def mem_rightclick(self):
        self.mem_sem.acquire()
        if self.base_address <= settings['data_max'] - MEMORY_SIZE:
            self.base_address += MEMORY_SIZE
        self.mem_sem.release()
        self.fill_mem()

    def mem_leftclick(self):
        self.mem_sem.acquire()
        if self.base_address >= MEMORY_SIZE:
            self.base_address -= MEMORY_SIZE
        self.mem_sem.release()
        self.fill_mem()

    def update_console(self, s="", clear=False):
        self.console_sem.acquire()
        if clear:
            self.out.setPlainText(s)
        else:
            self.out.insertPlainText(s)
        self.console_sem.release()

    def get_input(self, input_type):
        value, state = QInputDialog.getInt(self, 
                INPUT_MESSAGE[USER_INPUT_TYPE[input_type]], INPUT_LABEL)
        
        if state:
            self.intr.set_input(value)
        else:
            self.get_input(input_type)

    def add_breakpoint(self, cmd):
        self.controller.add_breakpoint(cmd)

    def remove_breakpoint(self, cmd):
        self.controller.remove_breakpoint((f'"{cmd[1]}"', cmd[2]))

    def launch_vt100(self):
        if self.vt100:
            self.vt100.close()
        self.vt100 = VT100(self.controller, self.changed_interp)

    def close_tab(self, i):
        if type(i) is bool:
            i = self.tabs.currentIndex()
        if self.tabs.tabText(i)[-1] == "*":
            choice = create_save_confirmation(self.tabs.widget(i).getFilename()).exec_()
            if choice == QMessageBox.Save:
                self.save_file(self.tabs.widget(i), i)
            elif choice == QMessageBox.Cancel:
                return
        if self.tabs.currentIndex() == i:
            self.update_button_status(start=False, step=False, backstep=False, pause=False)
            self.clear_tables()
        if self.tabs.widget(i).name in self.files:
            self.files.pop(self.tabs.widget(i).name)
        self.tabs.removeTab(i)
        self.file_count -= 1
        if self.file_count == 0:
            self.update_button_status(save=False, close=False, assemble=False, start=False, step=False, backstep=False, pause=False)

    def new_tab(self, wid: TextEdit=None):
        self.file_count += 1
        if not wid:
            wid = TextEdit(completer=self.comp, textChanged=self.update_dirty)
        self.tabs.addTab(wid, wid.getFilename())
        self.tabs.setCurrentWidget(wid)
        wid.setFocus()
        self.update_button_status(save=True, close=True, assemble=True)
        Highlighter(wid.document())

    def update_dirty(self):
        w = self.tabs.currentWidget()
        i = self.tabs.currentIndex()
        if w is not None:
            if w.is_new() or w.name in self.files:
                self.files[w.name] = True
                self.tabs.setTabText(i, f'{w.getFilename()} *')
            else:
                self.files[w.name] = False

    def update_button_status(self, **button_status):
        for tag, status in button_status.items():
            self.menu_items[tag].setEnabled(status)

    def closeEvent(self, event):
        unsaved_files = [i for i in range(self.file_count) if self.tabs.tabText(i)[-1] == "*"]
        if unsaved_files:
            choice = create_save_confirmation().exec_()
            if choice == QMessageBox.Cancel:
                event.ignore()
            else:
                if choice == QMessageBox.Save:
                    for i in unsaved_files:
                        self.save_file(self.tabs.widget(i), i)
                event.accept()

    def clear_tables(self):
        self.instr_grid.setRowCount(0) # remove instructions
        self.labels.setRowCount(0) # remove labels
        for cell in self.mem_vals: # clear memory
            cell.setText("")
        for r, cell in self.regs.items(): # reset registers
            cell.setText(WORD_HEX_FORMAT.format(settings.get(f"initial_{r}", 0)))

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow(app)
    app.exec_()