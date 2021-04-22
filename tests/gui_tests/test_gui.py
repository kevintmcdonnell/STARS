import sys
import unittest
from PySide2.QtCore import Qt
from PySide2.QtTest import QTest
from PySide2.QtWidgets import *

from gui.mainwindow import MainWindow
from gui.textedit import TextEdit
from constants import *
from threading import Thread
app = QApplication(sys.argv)

class GuiTest(unittest.TestCase):

    def setUp(self) -> None:
        self.form = MainWindow(app)

    def assemble(self, n):
        self.form.files[n] = False
        self.form.new_tab(wid=TextEdit(name=n), name=n)
        self.form.tabs.removeTab(0)
        self.form.assemble(n)

    def test_defaults(self):
        self.assertEqual(self.form.windowTitle(), "STARS")

        # register
        for r in self.form.regs:
            self.assertEqual(self.form.regs[r].text(), "0x00000000")

        # coproc flags
        for c in self.form.flags:
            self.assertEqual(c.isChecked(), False)

        # instr
        self.assertEqual(len(self.form.instrs), 0)
        self.assertEqual(len(self.form.pcs), 0)
        self.assertEqual(len(self.form.checkboxes), 0)
        self.assertEqual(self.form.instr_grid.columnCount(), 1)
        self.assertEqual(self.form.instr_grid.rowCount(), 1)

        # text edit tabs
        self.assertEqual(len(self.form.files), 0)
        self.assertEqual(self.form.tabs.tabText(0), "main.asm")
        self.assertEqual(len(self.form.tabs.currentWidget().toPlainText()), 0)

        # console
        self.assertEqual(len(self.form.out.toPlainText()), 0)

        # mem
        self.assertEqual(self.form.section_dropdown.currentText(), "Kernel")
        self.assertEqual(self.form.hdc_dropdown.currentText(), "Hexadecimal")
        count = 0
        for a in self.form.addresses:
            self.assertEqual(a.text(), f'0x{count:08x}')
            count += 16
        for m in self.form.mem_vals:
            self.assertEqual(m.text(), ' ')

        # program args
        self.assertEqual(len(self.form.pa.text()), 0)

    def test_change_click(self):
        self.assemble('test1.asm')

        self.form.reg_button.click()

        self.assertEqual(self.form.float, True)
        self.assertEqual(len(self.form.rlabels), len(REGS))
        for i in range(len(self.form.rlabels)):
            if i < len(F_REGS):
                self.assertEqual(self.form.rlabels[i].text(), f'{F_REGS[i]:5}')
            else:
                self.assertEqual(self.form.rlabels[i].text(), f'{REGS[i]:5}')

    def test_change_double_click(self):
        self.assemble('test1.asm')

        self.form.reg_button.click()
        self.form.reg_button.click()

        self.assertEqual(self.form.float, False)
        self.assertEqual(len(self.form.rlabels), len(REGS))
        for i in range(len(self.form.rlabels)):
            self.assertEqual(self.form.rlabels[i].text(), f'{REGS[i]:5}')

    def test_mem_up(self):
        self.assemble('test1.asm')

        self.form.mem_right.click()
        count = 256
        for a in self.form.addresses:
            self.assertEqual(a.text(), f'0x{count:08x}')
            count += 16

        for m in self.form.mem_vals:
            self.assertEqual(m.text(), '0x00 0x00 0x00 0x00')

    def test_mem_up_from_top(self):
        self.assemble('test1.asm')

        self.form.base_address = 0xffffffff
        self.form.mem_right.click()
        self.assertEqual(self.form.base_address, 0xffffffff)

    def test_mem_down(self):
        self.assemble('test1.asm')
        self.form.base_address = 256
        self.form.mem_left.click()
        count = 0
        for a in self.form.addresses:
            self.assertEqual(a.text(), f'0x{count:08x}')
            count += 16

        for m in self.form.mem_vals:
            self.assertEqual(m.text(), '0x00 0x00 0x00 0x00')

    def test_mem_down_from_bottom(self):
        self.assemble('test1.asm')

        self.form.mem_left.click()
        self.assertEqual(self.form.base_address, 0)

    def test_assemble(self):
        self.assemble('test1.asm')

        ig = self.form.instr_grid
        self.assertEqual(ig.rowCount(), 2)
        self.assertEqual(ig.itemAtPosition(0, 1).widget().text(), '0x00400000\tli $v0, 10 ( ori $v0, $0, 0x0000000a )')
        self.assertEqual(ig.itemAtPosition(1, 1).widget().text(), '0x00400004\tsyscall')

    def test_failed_assembly(self):
        self.assemble('failedAssembly.asm')

        ig = self.form.instr_grid
        self.assertEqual(ig.rowCount(), 1)
        o = self.form.out
        self.assertNotEqual(len(o.toPlainText()), 0)

    def test_clear_on_assemble(self):
        self.assemble('failedAssembly.asm')
        self.form.files = {}
        self.assemble('test1.asm')
        o = self.form.out
        self.assertEqual(len(o.toPlainText()), 0)

    def test_print(self):
        self.assemble('test_print.asm')
        self.form.controller.interp.out('1')

        o = self.form.out
        self.assertEqual(o.toPlainText(), '1')

    def test_coprocflags(self):
        self.assemble('test1.asm')

        self.form.controller.interp.condition_flags[0] = True
        self.form.controller.interp.step.emit()

        self.assertEqual(self.form.flags[0].checkState(), Qt.Checked)

    def test_regupdate(self):
        self.assemble('test1.asm')

        self.form.controller.interp.reg['$a0'] = 1
        self.form.controller.interp.step.emit()

        self.assertEqual(self.form.regs['$a0'].text(), '0x00000001')

    def test_regupdate_dec(self):
        self.assemble('test1.asm')

        self.form.hdc_dropdown.setCurrentIndex(1)

        self.form.controller.interp.reg['$a0'] = 1
        self.form.controller.interp.step.emit()

        self.assertEqual(self.form.regs['$a0'].text(), '1')

    def test_mem_update(self):
        self.assemble('test1.asm')

        self.form.controller.interp.mem.setByte(0, 1, admin=True)

        self.form.controller.interp.step.emit()

        self.assertEqual(self.form.mem_vals[0].text(), '0x00 0x00 0x00 0x01')

    def test_mem_update_dec(self):
        self.assemble('test1.asm')

        self.form.hdc_dropdown.setCurrentIndex(1)
        self.form.controller.interp.mem.setByte(0, 1, admin=True)

        self.form.controller.interp.step.emit()

        self.assertEqual(self.form.mem_vals[0].text(), '  0   0   0   1')

    def test_mem_update_dec(self):
        self.assemble('test1.asm')

        self.form.hdc_dropdown.setCurrentIndex(2)
        self.form.controller.interp.mem.setByte(0, ord('a'), admin=True)

        self.form.controller.interp.step.emit()

        self.assertEqual(self.form.mem_vals[0].text(), r'\0 \0 \0 a ')