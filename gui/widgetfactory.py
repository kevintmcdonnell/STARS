from typing import Callable, List, Tuple

from PySide2.QtCore import Qt
from PySide2.QtGui import QFont
from PySide2.QtWidgets import *

from constants import *

def create_breakpoint(text="") -> (QWidget, QCheckBox):
    '''Returns a checkbox, with the given text, centered inside of a widget.'''
    cell = QWidget()
    check = QCheckBox(text)
    layoutCheckbox = QHBoxLayout()
    layoutCheckbox.addWidget(check)
    layoutCheckbox.setAlignment(check, Qt.AlignCenter)
    layoutCheckbox.setContentsMargins(0, 0, 0, 0)
    cell.setLayout(layoutCheckbox)

    return cell, check

def create_cell(text: str="") -> QTableWidgetItem:
    '''Returns a cell for a QTableWidget.'''
    line = QTableWidgetItem(text)
    line.setFont(QFont("Courier New", 10))

    return line

def create_instruction(instruction: List[str], table: QTableWidget, row: int) -> List[QTableWidgetItem]:
    '''Returns a list of instruction cells inserted at the given row.''' 
    line = [create_cell(text) for text in instruction]
    for i, item in enumerate(line):
        table.setItem(row, i+1, item)

    return line

def create_table(rows: int, cols: int, labels: List[str], stretch_last: bool=False) -> QTableWidget:
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

def create_save_confirmation(filename: str="") -> QMessageBox:
    '''Creates a confirmation dialog for closing unsaved tabs.'''
    dialog = QMessageBox()
    if filename:
        dialog.setText(SAVE_SINGLE.format(filename))
    else: 
        dialog.setText(SAVE_MULTIPLE)
    dialog.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
    dialog.setDefaultButton(QMessageBox.Save)

    return dialog

def create_button(text: str, clicked_function: Callable[..., None]=None, 
            policy: Tuple[QSizePolicy, QSizePolicy]=None) -> QPushButton:
    '''Returns a button that triggers the provided function when clicked.'''
    button = QPushButton(text)
    button.clicked.connect(clicked_function)
    if policy:
        button.setSizePolicy(*policy)
    
    return button

def create_dropdown(items: List[str], select_function: Callable[..., None]=None) -> QComboBox:
    '''Returns a dropdown that calls the provided function when an item is selected.'''
    dropdown = QComboBox()
    dropdown.addItems(items)
    dropdown.currentTextChanged.connect(select_function)

    return dropdown