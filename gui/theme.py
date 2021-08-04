from copy import deepcopy
import json
import os 
import sys
from typing import Dict, Union

sys.path.append(os.getcwd())  # must be ran in sbumips directory (this is bc PYTHONPATH is weird in terminal)

from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import *

from constants import *
from gui.widgetfactory import create_box_layout, create_button, create_dropdown, create_widget

class ThemePicker(QDialog):
    def __init__(self, window: QMainWindow = None, theme: Dict = None) -> None:
        super().__init__()
        self.app = window
        self.preferences = theme
        self.current = self.app.theme if window else self.preferences[ON_START_THEME]
        themes = [theme for theme in self.preferences.keys() if theme != ON_START_THEME]
        
        self.theme_picker = create_dropdown(themes, self.update_ui)
        theme_sect = create_widget(create_box_layout(direction=QBoxLayout.LeftToRight,
                sections=[QLabel(THEME_SELECTOR_LABEL), self.theme_picker, 
                create_button(NEW_BUTTON, clicked_function=self.create_new_theme),
                create_button(DELETE_BUTTON, clicked_function=self.delete_theme),
                create_button(APPLY_PREFERENCES, clicked_function=self.apply_preferences),
                create_button(RESET_PREFERENCES, clicked_function=self.reset_preferences),
                create_button(SAVE_PREFERENCES, clicked_function=self.save_preferences)]))
        theme_sect.setParent(self)
        theme_sect.setFixedSize(DIALOG_WIDTH-2*DIALOG_MARGINS, DIALOG_BUTTON_HEIGHT)
        theme_sect.move(DIALOG_MARGINS,DIALOG_MARGINS)

        self.buttons = {} # buttons to control selectors
        self.tabs = QTabWidget(self)
        self.tabs.setFixedSize(DIALOG_WIDTH-2*DIALOG_MARGINS, DIALOG_HEIGHT-DIALOG_BUTTON_HEIGHT-2*DIALOG_MARGINS)
        self.tabs.move(DIALOG_MARGINS, 50)

        self.setFixedSize(DIALOG_WIDTH, DIALOG_HEIGHT)
        self.init_ui()
        self.update_ui(themes[0])

    def init_ui(self) -> None:
        '''Initialize the different categories along with their respective button selector.'''
        def select_color(category, field):
            new_value = QColorDialog.getColor()
            if category not in self.preferences[self.current]:
                self.preferences[self.current][category] = deepcopy(self.preferences[DEFAULT_THEME][category])
            if category == 'Highlighter':
                self.preferences[self.current][category][field]['color'] = new_value.name()
            else:
                self.preferences[self.current][category][field] = new_value.name()
            self.update_ui(self.current)

        for category in PREFERENCES_TABS:
            syntax_style = self.preferences[DEFAULT_THEME][category]
            syntax_list, buttons = [], []
            for key, value in syntax_style.items():
                button = create_button("", clicked_function=lambda s=None, c=category, k=key:select_color(c, k))
                buttons.append(button)
                syntax_list.append(create_box_layout(direction=QBoxLayout.LeftToRight,
                    sections=[QLabel(key), button]))
            layout = create_box_layout(direction=QBoxLayout.TopToBottom, sections=syntax_list)
            layout.setContentsMargins(10, 10, 10, 10)
            self.tabs.addTab(create_widget(layout), category)
            self.buttons[category] = buttons

    def update_ui(self, theme: str) -> None:
        '''Update the button colors to reflect values inside the json.'''
        def get_theme_attribute(choice: Dict[str, Union[Dict[str, str], str]], field: str) -> Union[Dict[str, str], str]:
            """Return the field in choice if defined otherwise return the default theme field."""
            return choice[field] if field in choice else self.preferences["default_theme"][field]
        
        self.current = theme
        choice = self.preferences[theme]
        for category in ['QPalette', 'Editor', 'Highlighter']:
            syntax_style = get_theme_attribute(choice, category)
            buttons = self.buttons[category]
            for i, value in enumerate(syntax_style.values()):
                if category == 'Highlighter':
                    value = value['color']
                    buttons[i].setText(value)
                    buttons[i].setStyleSheet(f"color: {value}")
                else:
                    buttons[i].setText("")
                    buttons[i].setStyleSheet(f"background-color: {value}")
        
    def create_new_theme(self) -> None:
        '''Create a new theme from the default theme.'''
        value, state = QInputDialog.getText(self, NEW_THEME, NEW_THEME_LABEL)
        if state:
            self.preferences[value] = deepcopy(self.preferences[DEFAULT_THEME])
            self.theme_picker.addItem(value)
            self.theme_picker.setCurrentIndex(self.theme_picker.count()-1)
            self.update_ui(value)
            self.apply_preferences()

    def delete_theme(self) -> None:
        '''Delete the current theme except if it is the default theme.'''
        if self.current != DEFAULT_THEME:
            confirmation = QMessageBox.question(self, '', DELETE_CONFIRMATION.format(self.current),
                                                QMessageBox.Yes | QMessageBox.No)
            if confirmation == QMessageBox.Yes:
                self.preferences.pop(self.current)
                self.theme_picker.removeItem(self.theme_picker.currentIndex())
                self.update_ui(self.theme_picker.currentText())
                self.apply_preferences()

    def apply_preferences(self) -> None:
        '''Apply the current preferences.'''
        if self.app:
            self.app.get_theme(self.current)
            self.app.update_theme()

    def reset_preferences(self) -> None:
        '''Reset the current preferences.'''
        with open(PREFERENCES_PATH) as f:
            self.preferences = json.load(f)
            self.app.preferences = self.preferences
        self.apply_preferences()
        self.update_ui(self.current)

    def save_preferences(self) -> None:
        '''Save the current preferences.'''
        with open(PREFERENCES_PATH, 'w') as f:
            json.dump(self.preferences, f, indent = 4)

    def closeEvent(self, event: QCloseEvent) -> None:
        '''Updates the theme of the GUI when the dialog is closed.'''
        self.apply_preferences()
        event.accept()

if __name__ == "__main__":
    app = QApplication()
    with open(PREFERENCES_PATH) as f:
        preferences = json.load(f)
    window = ThemePicker(theme=preferences)
    window.show()
    app.exec_()