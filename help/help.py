import csv
import os 
from typing import List
import sys

sys.path.append(os.getcwd())  # must be ran in sbumips directory (this is bc PYTHONPATH is weird in terminal)
from PySide2.QtCore import Qt
from PySide2.QtGui import QTextDocument
from PySide2.QtWidgets import *

from constants import HELP_TABS, HELP_TITLE
from gui.widgetfactory import create_cell, create_table

def create_tab(rows: List[str], header: List[str]) -> QTableWidget:
    '''Returns a table with csv row values inserted.'''
    table = create_table(len(rows), len(rows[0]), header, stretch_last=True)
    for row, values in enumerate(rows):
        for i, text in enumerate(values):
            table.setItem(row, i, create_cell((text.strip().replace('\\n', '\n'))))
    if not header:
        table.horizontalHeader().setVisible(False)
    table.resizeColumnsToContents()
    table.resizeRowsToContents()

    return table

class HelpWindow(QMainWindow):
    
    def __init__(self, app):
        super().__init__()
        self.setWindowTitle(HELP_TITLE)
        window = QTabWidget()
        for name, (filename, header) in HELP_TABS.items():
            with open(filename) as f:
                rows = [row for row in csv.reader(f)]
                table = create_tab(rows, header)
                window.addTab(table, name)
        self.setCentralWidget(window)
        
        self.show()
        self.resize(1080, 480)

if __name__ == "__main__":
    app = QApplication()
    window = HelpWindow(app)
    app.exec_()