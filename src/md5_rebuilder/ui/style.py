from __future__ import annotations

from md5_rebuilder.utils.paths import resources_dir

_RES = resources_dir()
DOWN_ARROW = (_RES / "chevron_down.xpm").as_posix() if _RES else ""
UP_ARROW = (_RES / "chevron_up.xpm").as_posix() if _RES else ""

THEMES = {
    "dark": {
        "bg": "#101318",
        "panel": "#181D25",
        "panel2": "#202632",
        "line": "#303846",
        "text": "#F3F6FA",
        "muted": "#9AA6B7",
        "accent": "#3DA5FF",
        "accent_hover": "#4FB0FF",
        "accent2": "#43D39E",
        "warn": "#FFB84D",
        "error": "#FF6074",
        "button_text": "#F3F6FA",
        "combo_button": "#2B3442",
        "combo_hover": "#344052",
        "combo_pressed": "#222A36",
        "combo_line": "#465163",
        "selection_text": "#FFFFFF",
    },
    "light": {
        "bg": "#F6F8FB",
        "panel": "#FFFFFF",
        "panel2": "#EEF2F7",
        "line": "#D7DEE8",
        "text": "#17202E",
        "muted": "#687386",
        "accent": "#1677D2",
        "accent_hover": "#0F68BD",
        "accent2": "#15A36B",
        "warn": "#B87400",
        "error": "#D93D50",
        "button_text": "#17202E",
        "combo_button": "#E5EBF3",
        "combo_hover": "#DCE5F0",
        "combo_pressed": "#CFDAE8",
        "combo_line": "#C4CEDB",
        "selection_text": "#FFFFFF",
    },
}


def build_app_style(theme: str = "dark") -> str:
    palette = THEMES.get(theme, THEMES["dark"])
    return f"""
QWidget {{
    background: {palette["bg"]};
    color: {palette["text"]};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}}
QLabel, QCheckBox {{
    background: transparent;
}}
QFrame#Panel {{
    background: {palette["panel"]};
    border: 1px solid {palette["line"]};
    border-radius: 8px;
}}
QLabel#Title {{
    font-size: 20px;
    font-weight: 800;
}}
QLabel#SectionTitle {{
    font-size: 14px;
    font-weight: 700;
}}
QLabel#Muted {{
    color: {palette["muted"]};
}}
QPushButton {{
    background: {palette["panel2"]};
    border: 1px solid {palette["line"]};
    border-radius: 6px;
    padding: 7px 10px;
    color: {palette["button_text"]};
}}
QPushButton:hover {{
    border-color: {palette["accent"]};
}}
QPushButton:pressed {{
    background: {palette["combo_pressed"]};
}}
QPushButton:disabled {{
    color: {palette["muted"]};
}}
QPushButton#Primary {{
    background: {palette["accent"]};
    border-color: {palette["accent"]};
    color: white;
    font-weight: 700;
}}
QPushButton#Primary:hover {{
    background: {palette["accent_hover"]};
}}
QPushButton#Danger {{
    background: {palette["error"]};
    border-color: {palette["error"]};
    color: white;
    font-weight: 700;
}}
QPushButton#AI {{
    background: {palette["panel"]};
    border-color: {palette["accent"]};
    color: {palette["accent"]};
    font-weight: 700;
}}
QPushButton#AI:hover {{
    background: {palette["panel2"]};
}}
QPushButton#Theme {{
    min-width: 76px;
}}
QPushButton#Reset {{
    min-width: 58px;
    padding: 5px 10px;
    border-color: {palette["combo_line"]};
    color: {palette["muted"]};
    font-weight: 700;
}}
QPushButton#Reset:hover {{
    color: {palette["accent"]};
    border-color: {palette["accent"]};
}}
QWidget#DragValueRow {{
    background: transparent;
}}
QStackedWidget#RateValueStack {{
    background: transparent;
    border: none;
}}
QWidget#DragValueRow QLabel {{
    color: {palette["text"]};
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {palette["panel2"]};
    border: 1px solid {palette["line"]};
    border-radius: 6px;
    padding: 6px 8px;
    color: {palette["text"]};
    selection-background-color: {palette["accent"]};
    selection-color: {palette["selection_text"]};
}}
QComboBox, QSpinBox, QDoubleSpinBox {{
    padding-right: 34px;
}}
QComboBox::drop-down {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 28px;
    margin: 1px;
    border: 1px solid {palette["combo_line"]};
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    background: {palette["combo_button"]};
}}
QComboBox::drop-down:hover {{
    background: {palette["combo_hover"]};
    border-color: {palette["accent"]};
}}
QComboBox::drop-down:pressed {{
    background: {palette["combo_pressed"]};
}}
QComboBox::down-arrow {{
    image: url("{DOWN_ARROW}");
    width: 9px;
    height: 6px;
}}
QComboBox QAbstractItemView {{
    background: {palette["panel"]};
    border: 1px solid {palette["line"]};
    border-radius: 6px;
    padding: 4px;
    color: {palette["text"]};
    selection-background-color: {palette["accent"]};
    selection-color: {palette["selection_text"]};
    outline: none;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 28px;
    margin: 1px 1px 0 0;
    border: 1px solid {palette["combo_line"]};
    border-bottom: none;
    border-top-right-radius: 5px;
    background: {palette["combo_button"]};
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 28px;
    margin: 0 1px 1px 0;
    border: 1px solid {palette["combo_line"]};
    border-bottom-right-radius: 5px;
    background: {palette["combo_button"]};
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {palette["combo_hover"]};
    border-color: {palette["accent"]};
}}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{
    background: {palette["combo_pressed"]};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url("{UP_ARROW}");
    width: 9px;
    height: 6px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url("{DOWN_ARROW}");
    width: 9px;
    height: 6px;
}}
QListWidget, QTextEdit {{
    background: {palette["panel2"]};
    border: 1px solid {palette["line"]};
    border-radius: 6px;
    color: {palette["text"]};
    selection-background-color: {palette["accent"]};
    selection-color: {palette["selection_text"]};
}}
QProgressBar {{
    background: {palette["panel2"]};
    border: 1px solid {palette["line"]};
    border-radius: 5px;
    text-align: center;
    color: {palette["text"]};
}}
QProgressBar::chunk {{
    background: {palette["accent2"]};
    border-radius: 5px;
}}
"""


APP_STYLE = build_app_style("dark")
