import os

from PyQt6.QtGui import QColor

DATA_DIR = "data"
ICON_PATH = os.path.join("images", "alohamora.ico")
SPELL_COLORS = {
    "Charm": QColor(173, 216, 230),  # light blue
    "Hex": QColor(255, 105, 97),  # soft red
    "Jinx": QColor(255, 215, 0),  # golden
    "Transfiguration": QColor(186, 85, 211),  # orchid
    "Counter-Spell": QColor(144, 238, 144),  # pale green
    "Default": QColor(245, 245, 245),  # light grey fallback
}
