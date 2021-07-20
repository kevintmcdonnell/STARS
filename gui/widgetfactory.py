from PySide2.QtCore import Qt
from PySide2.QtGui import QFont
from PySide2.QtWidgets import *

def create_breakpoint() -> (QWidget, QCheckBox):
    '''Returns a checkbox center inside of a widget.'''
    cell = QWidget()
    check = QCheckBox()
    layoutCheckbox = QHBoxLayout()
    layoutCheckbox.addWidget(check)
    layoutCheckbox.setAlignment(check, Qt.AlignCenter)
    layoutCheckbox.setContentsMargins(0, 0, 0, 0)
    cell.setLayout(layoutCheckbox)

    return cell, check

def create_instruction(text: str) -> QLineEdit:
    '''Returns a readonly single line textbox.'''
    line = QLineEdit(text)
    line.setFont(QFont("Courier New", 10))
    line.setReadOnly(True)
    line.setFrame(False)

    return line

def create_table(rows: int, cols: int, labels: [str], stretch_last: bool=False) -> QTableWidget:
    '''Returns a table with the provided rows, columns, and column labels.'''
    table = QTableWidget(rows, cols)
    if stretch_last:
        table.horizontalHeader().setStretchLastSection(True)
    else:
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.NoSelection)
    table.setHorizontalHeaderLabels(labels)
    table.horizontalHeader().sectionPressed.disconnect() 
    table.verticalHeader().setVisible(False)

    return table