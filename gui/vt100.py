from PySide2.QtWidgets import *
from PySide2.QtGui import QFont
from PySide2.QtCore import QTimer, Signal

from controller import Controller
from settings import settings
'''
Copyright 2020 Kevin McDonnell, Jihu Mun, and Ian Peitzsch

Developed by Kevin McDonnell (ktm@cs.stonybrook.edu),
Jihu Mun (jihu1011@gmail.com),
and Ian Peitzsch (irpeitzsch@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

class VT100(QWidget):
    def __init__(self, cont: Controller, start: Signal) -> None:
        super().__init__()
        self.controller = cont
        self.init_gui()
        self.reveal = False
        self.update_screen()
        start.connect(self.connect_to_interp)
        self.show()

    def connect_to_interp(self):
        self.controller.interp.mem_access.connect(self.update_screen)
        self.update_screen()

    def init_gui(self) -> None:
        self.setWindowTitle('MMIO Display')

        self.screen_arr = []
        grid = QGridLayout()
        grid.setSpacing(0)
        for i in range(25):
            row = []
            for j in range(80):
                q = QLabel('h')
                q.setFont(QFont('Courier New', 10))
                q.setStyleSheet(self.make_style(0x3D))
                grid.addWidget(q, i, j)
                row.append(q)
            self.screen_arr.append(row)

        self.button = QPushButton("View")
        self.button.clicked.connect(lambda : self.reset_reveal())
        grid.addWidget(self.button, 25, 79)
        self.setLayout(grid)

    def reset_reveal(self):
        self.reveal = not self.reveal

    def update_screen(self) -> None:
        if not self.controller.good():
            return

        # self.controller.interp.mem.dump()
        # return

        addr = 0xffff0000
        row = 0
        col = 0
        while addr < 0xffff0fA0:
            vtchar = self.controller.get_byte(addr)
            addr += 1
            vtcolor = self.controller.get_byte(addr)
            addr += 1
            q = self.screen_arr[row][col]
            if vtchar == 0:
                vtchar = 32
            q.setText(chr(vtchar))
            s = self.make_style(vtcolor)
            if self.reveal:
                s = self.make_style(0xF0)
            q.setStyleSheet(s)
            col += 1
            if col % 80 == 0:
                col = 0
                row += 1

    def make_style(self, byte: int) -> str:
        back = 'black'
        fore = 'green'

        up = (byte & 0xF0) >> 4
        low = byte & 0xF

        if up == 0:
            back = 'black'
        elif up == 1:
            back = 'darkRed'
        elif up == 2:
            back = 'darkGreen'
        elif up == 3:
            back = 'rgb(192,119,0)'
        elif up == 4:
            back = 'darkBlue'
        elif up == 5:
            back = "darkMagenta"
        elif up == 6:
            back = "darkCyan"
        elif up == 7:
            back = "gray"
        elif up == 8:
            back = "darkGray"
        elif up == 9:
            back = "red"
        elif up == 10:
            back = "green"
        elif up == 11:
            back = "yellow"
        elif up == 12:
            back = "blue"
        elif up == 13:
            back = "magenta"
        elif up == 14:
            back = "cyan"
        elif up == 15:
            back = "white"

        if low == 0:
            fore = 'black'
        elif low == 1:
            fore = 'darkRed'
        elif low == 2:
            fore = 'darkGreen'
        elif low == 3:
            fore = 'rgb(192,119,0)'
        elif low == 4:
            fore = 'darkBlue'
        elif low == 5:
            fore = "darkMagenta"
        elif low == 6:
            fore = "darkCyan"
        elif low == 7:
            fore = "gray"
        elif low == 8:
            fore = "darkGray"
        elif low == 9:
            fore = "red"
        elif low == 10:
            fore = "green"
        elif low == 11:
            fore = "yellow"
        elif low == 12:
            fore = "blue"
        elif low == 13:
            fore = "magenta"
        elif low == 14:
            fore = "cyan"
        elif low == 15:
            fore = "white"

        return f'QLabel {{background-color: {back}; color: {fore} }}'

