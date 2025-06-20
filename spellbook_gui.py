import json
import string
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SpellBook(QWidget):
    def __init__(self, spells_by_letter):
        super().__init__()
        self.setWindowTitle("Hogwarts Spellbook")
        self.resize(600, 500)

        self.spells_by_letter = spells_by_letter
        self.tabs = QTabWidget()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a spell…")

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.tabs)

        self.list_widgets = {}  # Track list widgets by tab

        for letter in string.ascii_uppercase:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            list_widget = QListWidget()

            spells = spells_by_letter.get(letter, [])
            for spell in spells:
                item = QListWidgetItem(f"{spell['name']} — {spell['description']}")
                list_widget.addItem(item)

            tab_layout.addWidget(list_widget)
            self.tabs.addTab(tab, letter)
            self.list_widgets[letter] = (list_widget, spells)

        self.search_bar.textChanged.connect(self.filter_current_tab)

    def filter_current_tab(self, text):
        current_letter = self.tabs.tabText(self.tabs.currentIndex())
        list_widget, original_spells = self.list_widgets[current_letter]
        list_widget.clear()
        filtered = [s for s in original_spells if text.lower() in s["name"].lower()]
        for spell in filtered:
            item = QListWidgetItem(f"{spell['name']} — {spell['description']}")
            list_widget.addItem(item)


def load_spells(filename="spells.json"):
    with open(filename, encoding="utf-8") as f:
        data = json.load(f)
    grouped = {}
    for spell in data:
        first_letter = spell["name"][0].upper()
        grouped.setdefault(first_letter, []).append(spell)
    return grouped


if __name__ == "__main__":
    app = QApplication(sys.argv)
    spells = load_spells()
    window = SpellBook(spells)
    window.show()
    sys.exit(app.exec())
