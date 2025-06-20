import json
import string
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SpellBook(QWidget):
    def __init__(self, spells_by_letter):
        super().__init__()
        self.setWindowTitle("Hogwarts Spellbook")
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        for letter in string.ascii_uppercase:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            list_widget = QListWidget()

            for spell in spells_by_letter.get(letter, []):
                item = QListWidgetItem(f"{spell['name']} — {spell['description']}")
                list_widget.addItem(item)

            tab_layout.addWidget(list_widget)
            tabs.addTab(tab, letter)


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
