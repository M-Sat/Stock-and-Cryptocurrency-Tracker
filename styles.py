"""
UI styles and constants.
"""

# Main stylesheet for the application
MAIN_STYLESHEET = """
    QMainWindow { background-color: #0b0e14; }
    QTabWidget::pane { border: none; background-color: #0b0e14; }
    QTabBar::tab {
        background: #1a1d2e;
        color: #888eb0;
        padding: 15px 40px;
        font-weight: bold;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 5px;
    }
    QTabBar::tab:selected {
        background: #007bff;
        color: white;
    }
    QLineEdit {
        background-color: #1a1d2e; color: white;
        border: 1px solid #3f445e; border-radius: 8px;
        padding: 12px; font-size: 16px;
    }
    QPushButton {
        background-color: #007bff; color: white;
        border-radius: 8px; padding: 12px 25px;
        font-weight: bold; font-size: 14px;
    }
    QPushButton:hover { background-color: #0056b3; }
    QListWidget {
        background-color: #161926; border: 1px solid #252940;
        border-radius: 10px; color: #e0e0e0; font-size: 14px;
        outline: none;
    }
    QListWidget::item { padding: 15px; border-bottom: 1px solid #252940; }
    QListWidget::item:selected {
        background-color: #1e2235; color: #007bff; border-left: 4px solid #007bff;
    }
    #PriceLabel { font-size: 96px; font-weight: bold; color: #ffffff; }
    #SymbolLabel { font-size: 24px; color: #888eb0; letter-spacing: 4px; }
    #NameLabel { font-size: 42px; font-weight: bold; color: #ffffff; }
    #Card {
        background-color: #161926; border: 1px solid #252940;
        border-radius: 20px; padding: 30px;
    }
    QLabel { color: #a0a0a0; }
"""

# Period button styles
PERIOD_BUTTON_NORMAL = """
    QPushButton {
        background-color: #252940; color: #888eb0;
        border-radius: 5px; padding: 6px 12px;
        font-weight: bold; font-size: 12px;
        border: 1px solid #3f445e;
    }
    QPushButton:hover { background-color: #1e2235; }
"""

PERIOD_BUTTON_SELECTED = """
    QPushButton {
        background-color: #007bff; color: white;
        border-radius: 5px; padding: 6px 12px;
        font-weight: bold; font-size: 12px;
        border: 1px solid #007bff;
    }
"""

# Dialog styles
DIALOG_STYLESHEET = """
    QDialog { background-color: #161926; }
    QLabel { color: #a0a0a0; }
    QSpinBox { background-color: #1a1d2e; color: white; border: 1px solid #3f445e; padding: 8px; border-radius: 5px; }
    QPushButton { background-color: #007bff; color: white; border-radius: 5px; padding: 8px 20px; font-weight: bold; }
    QPushButton:hover { background-color: #0056b3; }
"""

# Portfolio table styles
PORTFOLIO_TABLE_STYLESHEET = """
    QTableWidget {
        background-color: #161926; border: 1px solid #252940;
        border-radius: 10px; color: #e0e0e0;
    }
    QHeaderView::section {
        background-color: #1a1d2e; color: #888eb0;
        padding: 8px; border: none; font-weight: bold;
    }
    QTableWidget::item {
        padding: 8px; border-bottom: 1px solid #252940;
    }
"""

# Remove button style
REMOVE_BUTTON_STYLESHEET = """
    QPushButton {
        background-color: #ff4d4d; color: white;
        border-radius: 5px; padding: 6px 12px;
        font-weight: bold; font-size: 10px;
        border: none;
    }
    QPushButton:hover { background-color: #e63946; }
"""

# Alert button style (same as remove button)
ALERT_BUTTON_STYLESHEET = """
    QPushButton {
        background-color: #ff4d4d; color: white;
        border-radius: 5px; padding: 6px 12px;
        font-weight: bold; font-size: 10px;
        border: none;
    }
    QPushButton:hover { background-color: #e63946; }
"""

# Refresh button style
REFRESH_BUTTON_STYLESHEET = """
    QPushButton {
        background-color: #007bff; color: white;
        border-radius: 8px; padding: 10px 20px;
        font-weight: bold; font-size: 12px;
    }
    QPushButton:hover { background-color: #0056b3; }
"""

# Colors
COLOR_POSITIVE = "#00ff88"
COLOR_NEGATIVE = "#ff4d4d"
COLOR_SECONDARY = "#888eb0"
COLOR_TEXT_DARK = "#a0a0a0"
COLOR_CARD = "#161926"
COLOR_BORDER = "#252940"

# Sizes
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 900
GRAPH_TOOLTIP_FONT_SIZE = 12
RESULTS_LIST_MAX_HEIGHT = 180
PERIOD_BUTTON_MAX_WIDTH = 60
