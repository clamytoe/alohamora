import json
import string
import sys
import webbrowser

from PyQt6.QtWidgets import (
    QApplication,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from rapidfuzz import fuzz, process


class SpellBook(QWidget):
    def __init__(self, spells_by_letter):
        super().__init__()
        self.setWindowTitle("Hogwarts Spellbook")
        self.resize(600, 500)

        self.tabs = QTabWidget()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a spell…")

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.tabs)

        self.spells_by_letter = spells_by_letter
        self.all_spells = [s for spells in spells_by_letter.values() for s in spells]
        self.list_widgets = {}

        for letter in string.ascii_uppercase:
            tab = QWidget()
            layout_tab = QVBoxLayout(tab)
            list_widget = QListWidget()

            spells = spells_by_letter.get(letter, [])
            for spell in spells:
                item = QListWidgetItem(f"{spell['name']} — {spell['description']}")
                item.setToolTip(spell["link"] or "No link available")
                list_widget.addItem(item)

            layout_tab.addWidget(list_widget)
            self.tabs.addTab(tab, letter)
            self.list_widgets[letter] = (list_widget, spells)

            list_widget.itemDoubleClicked.connect(
                self.create_double_click_handler(spells)
            )

        self.search_bar.textChanged.connect(self.filter_across_tabs)

    def create_double_click_handler(self, spell_list):
        def handler(item):
            name = item.text().split(" — ")[0]
            for spell in spell_list:
                if spell["name"] == name and spell.get("link"):
                    webbrowser.open(spell["link"])
                    break

        return handler

    def filter_across_tabs(self, text):
        text = text.strip().lower()
        if not text:
            self.reset_all_tabs()
            return

        # Use fuzzy matching for broader suggestions
        spell_name_map = {s["name"]: s for s in self.all_spells}
        matches = process.extract(
            query=text,
            choices=list(spell_name_map.keys()),
            scorer=fuzz.WRatio,
            limit=5,
            score_cutoff=65,
        )
        matched_names = set(name.lower() for name, _, _ in matches)

        first_exact = None
        for _, (list_widget, spell_list) in self.list_widgets.items():
            list_widget.clear()
            filtered = [
                s
                for s in spell_list
                if s["name"].lower().startswith(text)
                or s["name"].lower() in matched_names
            ]
            for spell in filtered:
                item = QListWidgetItem(f"{spell['name']} — {spell['description']}")
                item.setToolTip(spell["link"] or "No link available")
                list_widget.addItem(item)

                if not first_exact and spell["name"].lower().startswith(text):
                    first_exact = spell

        if first_exact:
            first_letter = first_exact["name"][0].upper()
            index = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".index(first_letter)
            self.tabs.setCurrentIndex(index)

    def reset_all_tabs(self):
        for letter, (list_widget, spell_list) in self.list_widgets.items():
            list_widget.clear()
            for spell in spell_list:
                item = QListWidgetItem(f"{spell['name']} — {spell['description']}")
                item.setToolTip(spell["link"] or "No link available")
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
