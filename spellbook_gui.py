import json
import math
import os
import random
import re
import string
import sys
import time
from collections import deque

import requests
from bs4 import BeautifulSoup
from PyQt6.QtCore import QPointF, Qt, QTimer
from PyQt6.QtGui import QColor, QCursor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from rapidfuzz import fuzz, process

DATA_DIR = "data"
ICON_PATH = os.path.join("images", "alohamora.ico")


class SpellBook(QWidget):
    def __init__(self, spells_by_letter):
        super().__init__()
        self.setAutoFillBackground(True)
        self.setWindowTitle("Hogwarts Spellbook")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setStyleSheet("background-color: white;")
        self.resize(900, 550)

        self.spells_by_letter = spells_by_letter
        self.all_spells = [s for spells in spells_by_letter.values() for s in spells]

        self.tabs = QTabWidget()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a spell…")
        reset_btn = QPushButton("⟳")
        reset_btn.setFixedWidth(30)
        reset_btn.setToolTip("Reset Search and Refresh View")
        reset_btn.clicked.connect(self.reset_ui)

        search_layout = QHBoxLayout()
        search_layout.addWidget(reset_btn)
        search_layout.addWidget(self.search_bar)

        self.preview = QTextBrowser()
        self.sparkle_overlay = SparkleOverlay(self.preview.viewport())
        self.preview.viewport().installEventFilter(self)
        self.preview.viewport().setMouseTracking(True)
        self.sparkle_overlay.resize(self.preview.viewport().size())
        self.sparkle_overlay.show()
        self.preview.setOpenExternalLinks(True)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(search_layout)

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

        self.wand_cursor = self.create_wand_cursor("wand-cursor.png")
        self.glowing_wand_cursor = self.create_wand_cursor("glowing-wand-cursor.png")

        self.preview.viewport().setCursor(self.wand_cursor)
        self.search_bar.setFocus()

    def create_wand_cursor(self, wand_name):
        cursor_path = os.path.join(os.path.dirname(__file__), "images", wand_name)
        wand_pixmap = QPixmap(cursor_path).scaled(
            32,
            32,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        wand_cursor = QCursor(wand_pixmap, 0, 0)
        return wand_cursor

    def create_single_click_handler(self, spell_list):
        def handler(item):
            name = item.text().split(" — ")[0]
            for spell in spell_list:
                if spell["name"] == name:
                    summary = self.get_spell_summary(spell)
                    self.preview.setHtml(summary)
                    break

        return handler

    def eventFilter(self, source, event):
        if source == self.preview.viewport():
            if event.type() == event.Type.MouseMove:
                now = time.time()
                pos = event.position().toPoint()
                self.sparkle_overlay.mouse_history.append((pos.x(), pos.y(), now))
                self.sparkle_overlay.trigger_sparkle(event.position())
                cursor = self.preview.cursorForPosition(event.position().toPoint())
                fmt = cursor.charFormat()
                if fmt.isAnchor():
                    source.setCursor(self.glowing_wand_cursor)
                else:
                    source.setCursor(self.wand_cursor)

            elif event.type() == event.Type.MouseButtonPress:
                pos = event.position()
                self.sparkle_overlay.burst_sparkles(pos.x(), pos.y())
        return super().eventFilter(source, event)

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

        paragraphs = soup.select("div.mw-parser-output > p")
        if len(paragraphs) > 1:
            paragraph = soup.select("div.mw-parser-output > p")[1]
        else:
            paragraph = soup.select("div.mw-parser-output > p")[0]
        first_para = paragraph.get_text(strip=False) if paragraph else ""
        para = re.sub(r"\[\d+\]", "", first_para)

        names = []
        values = []
        for section in soup.select("aside.portable-infobox > section"):
            for div in section.select("div.pi-item"):
                n = div.text.lstrip().rstrip()
                n = re.sub(r"\[\d+\]", "", n)
                if "\n" in n:
                    n = n.split("\n")[0]
                names.append(n)
            for div in section.select("div.pi-data-value"):
                if div.select("img"):
                    i = div.select("img")[0]
                    img_url = i["src"].split("?")[0]  # type: ignore
                    img_name = i["data-image-name"]
                    img_path = os.path.join(DATA_DIR, "images", img_name)  # type: ignore
                    img_tag = ""

                    # Download and save if not already cached
                    os.makedirs(os.path.dirname(img_path), exist_ok=True)
                    if not os.path.exists(img_path):
                        try:
                            resp = requests.get(img_url)
                            resp.raise_for_status()
                            with open(img_path, "wb") as f:
                                f.write(resp.content)
                        except Exception as e:
                            print(f"Image download failed: {e}")
                        else:
                            print(f"Saved image: {img_path}")

                    if os.path.exists(img_path):
                        img_tag = (
                            f'<img src="{img_path}" alt="{img_name}" width="70" />'
                        )
                    else:
                        img_tag = f'<img src="{img_url}" alt="{img_name}" width="70" />'
                    values.append(img_tag)
                else:
                    d = re.sub(r"\[\d+\]", "", div.text)
                    values.append(d)
        aside = dict(zip(names, values))

        return f"""
            <html><body style="background-color: #fdf6e3;">
            <h1 align="center">{name}</h1>
            <div style="text-align: center; margin-bottom: 10px;">
                <div style="
                    display: inline-block;
                    padding: 6px;
                    border: 2px solid #8B4513;
                    background-color: #fdf6e3;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
                    border-radius: 8px;">
                    {aside.get("Hand movement", "")}
                </div>
            </div>
            <h2>{spell['description']}</h2>
            <p>
                <table>
                    <tr>
                        <th align="right">Category</th>
                        <td style="padding-left: 10px;">{aside.get("Incantation", "")}</td>
                    </tr>
                    <tr>
                        <th align="right">Type</th>
                        <td style="padding-left: 10px;">{aside.get("Type", "")}</td>
                    </tr>
                    <tr>
                        <th align="right">Light</th>
                        <td style="padding-left: 10px;">{aside.get("Light", "")}</td>
                    </tr>
                    <tr>
                        <th align="right">Effect</th>
                        <td style="padding-left: 10px;">{aside.get("Effect", "")}</td>
                    </tr>
                </table>
            </p>
            <hr>
            <p>{para or '<i>No summary found on page.</i>'}</p>
            <p><a href="{link}">View More</a></p>
            </body></html>
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

    def handle_link_hover(self, link):
        if link:
            self.preview.viewport().setCursor(self.glowing_wand_cursor)
        else:
            self.preview.viewport().setCursor(self.wand_cursor)

    def reset_all_tabs(self):
        for letter, (list_widget, spell_list) in self.list_widgets.items():
            list_widget.clear()
            for spell in spell_list:
                item = QListWidgetItem(f"{spell['name']} — {spell['description']}")
                item.setToolTip(spell["link"] or "No link available")
                list_widget.addItem(item)

    def reset_ui(self):
        self.search_bar.clear()
        self.reset_all_tabs()
        self.preview.clear()
        self.tabs.setCurrentIndex(0)
        self.search_bar.setFocus()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "sparkle_overlay"):
            self.sparkle_overlay.resize(self.preview.viewport().size())


class SparkleOverlay(QWidget):
    def __init__(self, target_widget):
        super().__init__(target_widget)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.sparkles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_sparkles)
        self.timer.start(16)

        self.sparkle_colors = [
            QColor(255, 223, 0, 255),  # gold
            QColor(173, 216, 230, 255),  # light blue
            QColor(255, 182, 193, 255),  # pink
            QColor(144, 238, 144, 255),  # pale green
            QColor(221, 160, 221, 255),  # lavender
        ]
        self.mouse_history = deque(maxlen=5)  # from collections import deque

    def update_sparkles(self):
        now = time.time()
        dt = 0.016  # ~60 FPS for smooth motion
        width = self.parent().width()
        height = self.parent().height()
        updated = []

        for x, y, vx, vy, t, color in self.sparkles:
            age = now - t
            if age < 0.75:
                # Move sparkle
                x += vx * dt
                y += vy * dt

                # Bounce on horizontal edges
                if x <= 0 or x >= width:
                    vx *= -1
                    x = max(0, min(width, x))

                # Bounce on vertical edges
                if y <= 0 or y >= height:
                    vy *= -1
                    y = max(0, min(height, y))

                updated.append([x, y, vx, vy, t, color])

        self.sparkles = updated
        self.update()

    def add_sparkle(self, x, y):
        vx, vy = self.estimate_velocity()
        friction = 0.92  # 0.9–0.98 is a good sweet spot
        vx *= friction
        vy *= friction
        color = random.choice(self.sparkle_colors)
        self.sparkles.append([x, y, vx, vy, time.time(), color])

    def burst_sparkles(self, x, y, count=24):
        now = time.time()
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 140)  # shoot outward with force
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(self.sparkle_colors)
            self.sparkles.append([x, y, vx, vy, now, color])

    def estimate_velocity(self):
        if len(self.mouse_history) < 2:
            return 0.0, 0.0
        (x1, y1, t1), (x2, y2, t2) = self.mouse_history[-2], self.mouse_history[-1]
        dt = max(t2 - t1, 1e-5)
        scale = 0.5  # Tune this multiplier for "whip speed"
        return scale * (x2 - x1) / dt, scale * (y2 - y1) / dt

    def trigger_sparkle(self, pos):
        self.add_sparkle(pos.x(), pos.y())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        now = time.time()
        for x, y, _, _, t, color in self.sparkles:
            age = now - t
            alpha = int(255 * (1 - age / 0.5))
            if color.isValid():
                c = QColor(color.red(), color.green(), color.blue(), alpha)
                painter.setBrush(c)
                painter.setPen(Qt.PenStyle.NoPen)
                size = 2 + 2 * (1 - age / 0.75)  # start large, shrink over life
                painter.drawEllipse(QPointF(x, y), size, size)


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
    app.setWindowIcon(QIcon(ICON_PATH))

    spells = load_spells()
    window = SpellBook(spells)
    window.show()
    sys.exit(app.exec())
