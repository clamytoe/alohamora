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

        self.list_widgets = {}  # Track widgets and data

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

        self.search_bar.textChanged.connect(self.filter_across_tabs)

    def filter_across_tabs(self, text):
        text = text.strip().lower()
        if not text:
            self.reset_all_tabs()
            return

        first_exact_match = None
        for letter, (list_widget, all_spells) in self.list_widgets.items():
            list_widget.clear()
            filtered = [s for s in all_spells if text in s["name"].lower()]
            for spell in filtered:
                item = QListWidgetItem(f"{spell['name']} — {spell['description']}")
                list_widget.addItem(item)

                # Record exact match on name start
                if not first_exact_match and spell["name"].lower().startswith(text):
                    first_exact_match = spell

        if first_exact_match:
            first_letter = first_exact_match["name"][0].upper()
            if first_letter in self.list_widgets:
                index = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".index(first_letter)
                self.tabs.setCurrentIndex(index)

    def reset_all_tabs(self):
        for letter, (list_widget, all_spells) in self.list_widgets.items():
            list_widget.clear()
            for spell in all_spells:
                list_widget.addItem(
                    QListWidgetItem(f"{spell['name']} — {spell['description']}")
                )


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
