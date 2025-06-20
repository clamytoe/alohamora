import json
import os
import re
import string
import sys

import requests
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from rapidfuzz import fuzz, process

DATA_DIR = "data"


class SpellBook(QWidget):
    def __init__(self, spells_by_letter):
        super().__init__()
        self.setWindowTitle("Hogwarts Spellbook")
        self.resize(900, 500)

        self.spells_by_letter = spells_by_letter
        self.all_spells = [s for spells in spells_by_letter.values() for s in spells]

        self.tabs = QTabWidget()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a spell…")
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)

        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.search_bar)

        split_layout = QHBoxLayout()
        split_layout.addWidget(self.tabs, 3)
        split_layout.addWidget(self.preview, 5)
        main_layout.addLayout(split_layout)

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

            list_widget.itemClicked.connect(self.create_single_click_handler(spells))

            layout_tab.addWidget(list_widget)
            self.tabs.addTab(tab, letter)
            self.list_widgets[letter] = (list_widget, spells)

        self.search_bar.textChanged.connect(self.filter_across_tabs)

    def create_single_click_handler(self, spell_list):
        def handler(item):
            name = item.text().split(" — ")[0]
            for spell in spell_list:
                if spell["name"] == name:
                    summary = self.get_spell_summary(spell)
                    self.preview.setHtml(summary)
                    break

        return handler

    def get_spell_summary(self, spell):
        name = spell["name"]
        link = spell.get("link")
        summary = "<i>No additional information available.</i>"

        if not link:
            return f"<b>{name}</b><br>{spell['description']}<br><br>{summary}"

        filename = os.path.join(DATA_DIR, f"{name}.html")

        # Fetch and cache if needed
        if not os.path.exists(filename):
            try:
                resp = requests.get(link)
                resp.raise_for_status()
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(resp.text)
            except Exception:
                err = f"<b>{name}</b><br>{spell['description']}<br>"
                err += "<br><i>Failed to fetch page.</i>"
                return err

        with open(filename, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        paragraph = soup.select("div.mw-parser-output > p")[1]
        first_para = paragraph.get_text(strip=False) if paragraph else ""
        para = re.sub(r"\[\d+\]", "", first_para)

        return f"""
            <h3>{name}</h3>
            <p>{spell['description']}</p>
            <hr>
            <p>{para or '<i>No summary found on page.</i>'}</p>
            <p><a href="{link}">View More</a></p>
        """

    def filter_across_tabs(self, text):
        text = text.strip().lower()
        if not text:
            self.reset_all_tabs()
            return

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
                or s["name"].lower() in matched_names  # noqa
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
