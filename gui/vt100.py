from PySide2.QtWidgets import *
from PySide2.QtGui import QFont
from PySide2.QtCore import QTimer

from controller import Controller
from settings import settings

class VT100(QWidget):
    def __init__(self, cont: Controller) -> None:
        super().__init__()
        self.controller = cont
        self.init_gui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_screen)
        self.timer.start(100)
        self.reveal = False
        self.update_screen()
        self.show()

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

