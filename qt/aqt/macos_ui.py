# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Shared macOS appearance for native widgets and embedded application pages."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aqt.qt import QTabWidget


def widget_styles(night: bool, down_icon: str, up_icon: str) -> str:
    if night:
        canvas, surface, text = "#202022", "#2b2b2e", "#f5f5f7"
        secondary, border, hover = "#aaaab1", "#48484c", "#363639"
        selection, accent = "#263e5d", "#75b5ff"
    else:
        canvas, surface, text = "#f5f5f7", "#ffffff", "#1d1d1f"
        secondary, border, hover = "#65656b", "#dcdce0", "#ededf0"
        selection, accent = "#e8f1fc", "#0067d9"

    # Keep platform menu bars, checkbox/radio indicators, scrollbars, and
    # window decorations native. Scope styling to ordinary application controls.
    return f"""
QDialog, QMainWindow {{ background-color: {canvas}; }}
QLabel {{ color: {text}; }}
QLabel:disabled {{ color: {secondary}; }}
QPushButton {{
    min-height: 22px;
    padding: 3px 12px;
    border: 1px solid {border};
    border-radius: 7px;
    background-color: {surface};
    color: {text};
}}
QPushButton:hover {{ background-color: {hover}; }}
QPushButton:pressed, QPushButton:checked {{ background-color: {selection}; }}
QPushButton:default {{
    border-color: {accent};
}}
QDialogButtonBox QPushButton:default {{ background-color: #007aff; color: white; }}
QDialogButtonBox QPushButton:default:hover {{ background-color: #0069df; }}
QPushButton:focus {{ border: 1px solid {accent}; }}
QPushButton:disabled {{ color: {secondary}; background-color: {canvas}; }}
QPushButton:flat {{ border: none; background: transparent; }}
QToolButton {{
    padding: 5px;
    border: 1px solid transparent;
    border-radius: 6px;
    color: {text};
}}
QToolButton:hover {{ background-color: {hover}; border-color: {border}; }}
QToolButton:checked {{ background-color: {selection}; border-color: {border}; }}
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    border-radius: 7px;
    padding: 5px 7px;
    selection-background-color: {selection};
    selection-color: {text};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border-color: {accent}; }}
QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
    color: {secondary}; background-color: {canvas};
}}
QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit {{
    min-height: 20px;
    padding: 2px 7px;
    border: 1px solid {border};
    border-radius: 6px;
    background-color: {surface};
    color: {text};
}}
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {accent}; }}
QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{ color: {secondary}; }}
QComboBox {{ padding-right: 25px; }}
QComboBox::drop-down {{ border: none; width: 24px; background: transparent; }}
QComboBox::down-arrow {{ image: url("{down_icon}"); width: 13px; height: 13px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    border: none; width: 20px; background: transparent;
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url("{up_icon}"); width: 10px; height: 10px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url("{down_icon}"); width: 10px; height: 10px;
}}
QAbstractItemView {{
    background-color: {surface};
    alternate-background-color: {canvas};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    selection-background-color: {selection};
    selection-color: {text};
}}
QTreeView::item, QListView::item {{ padding: 4px; border-radius: 5px; }}
QAbstractItemView::item:hover {{ background-color: {hover}; }}
QAbstractItemView::item:selected {{ background-color: {selection}; color: {text}; }}
QHeaderView::section {{
    background-color: {canvas};
    color: {secondary};
    padding: 7px 8px;
    border: none;
    border-bottom: 1px solid {border};
}}
QTableView {{ gridline-color: {border}; }}
QTableCornerButton::section {{ background-color: {canvas}; border: none; }}
QDockWidget#Sidebar {{ background-color: {canvas}; border: none; }}
QDockWidget#Sidebar QTreeView {{
    background-color: {canvas};
    border: none;
    border-radius: 0;
    padding: 6px;
}}
QTabWidget::pane {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 9px;
    top: -1px;
}}
QTabBar::tab {{
    background-color: {canvas};
    color: {secondary};
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 10px;
    margin: 3px 2px;
}}
QTabBar::tab:selected {{
    background-color: {surface};
    color: {text};
    border-color: {border};
}}
QTabBar::tab:hover {{ color: {text}; }}
QGroupBox {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 9px;
    margin-top: 12px;
    padding: 8px 10px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    left: 10px;
    color: {secondary};
}}
QDialogButtonBox {{ padding-top: 6px; button-layout: 1; }}
QStatusBar {{ background-color: {canvas}; color: {secondary}; }}
QSplitter::handle {{ background-color: {border}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}
"""


def prepare_preferences_tabs(tabs: QTabWidget) -> None:
    """Let settings pages scroll instead of forcing a window taller than a laptop."""
    from aqt.qt import QFrame, QScrollArea

    current = tabs.currentIndex()
    for index in range(tabs.count()):
        page = tabs.widget(index)
        assert page is not None
        title = tabs.tabText(index)
        tabs.removeTab(index)
        scroll = QScrollArea(tabs)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        tabs.insertTab(index, scroll, title)
    tabs.setCurrentIndex(current)


def web_styles() -> str:
    # Body-scoped variables also reach Svelte components and their popovers.
    # Card bodies always carry .card; never restyle their content or templates.
    return """
body.isMac:not(.card) {
    --mac-background: #f5f5f7;
    --mac-surface: #ffffff;
    --mac-text: #1d1d1f;
    --mac-secondary: #65656b;
    --mac-border: #dcdce0;
    --mac-hover: #ededf0;
    --mac-selection: #e8f1fc;
    --mac-accent: #0067d9;
    --canvas: var(--mac-background);
    --canvas-elevated: var(--mac-surface);
    --canvas-inset: var(--mac-surface);
    --canvas-overlay: var(--mac-surface);
    --canvas-code: var(--mac-surface);
    --fg: var(--mac-text);
    --fg-subtle: var(--mac-secondary);
    --fg-link: var(--mac-accent);
    --border: var(--mac-border);
    --border-subtle: var(--mac-border);
    --border-focus: var(--mac-accent);
    --border-radius: 7px;
    --border-radius-medium: 10px;
    --border-radius-large: 10px;
    --bs-body-font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    --bs-body-color: var(--mac-text);
    --bs-body-bg: var(--mac-background);
    --bs-border-color: var(--mac-border);
    --bs-secondary-color: var(--mac-secondary);
    color: var(--mac-text);
    background-color: var(--mac-background);
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    -webkit-font-smoothing: antialiased;
}
body.isMac.nightMode:not(.card) {
    --mac-background: #202022;
    --mac-surface: #2b2b2e;
    --mac-text: #f5f5f7;
    --mac-secondary: #aaaab1;
    --mac-border: #48484c;
    --mac-hover: #363639;
    --mac-selection: #263e5d;
    --mac-accent: #75b5ff;
}
body.isMac:not(.card) :is(button, input, select) { font-family: inherit; }
body.isMac:not(.card) :is(button, .btn) {
    border-radius: 7px;
    box-shadow: none;
    font-weight: 500;
    transition-duration: 0.1s;
}
body.isMac:not(.card) button:not(.btn, .btn-close, .icon-button) {
    background: var(--mac-surface);
    color: var(--mac-text);
    border-color: var(--mac-border);
}
body.isMac:not(.card) button:not(.btn, .btn-close, .icon-button):hover {
    background: var(--mac-hover);
}
body.isMac:not(.card) :is(.btn-primary, .btn-primary:hover) {
    --bs-btn-bg: #007aff;
    --bs-btn-border-color: #007aff;
    --bs-btn-hover-bg: #0069df;
    --bs-btn-hover-border-color: #0069df;
    --bs-btn-active-bg: #0069df;
    --bs-btn-color: white;
}
body.isMac:not(.card) :is(.form-control, .form-select, input[type=text], input[type=number], select) {
    background-color: var(--mac-surface);
    color: var(--mac-text);
    border: 1px solid var(--mac-border);
    border-radius: 7px;
    min-height: 28px;
}
body.isMac:not(.card) :is(input, select, textarea):focus-visible {
    outline: 2px solid var(--mac-accent);
    outline-offset: 2px;
}
body.isMac:not(.card) .spin-box {
    border-color: var(--mac-border);
    border-radius: 7px;
    background: var(--mac-surface);
}
body.isMac:not(.card) .spin-box input {
    border: none;
    background: transparent;
    outline: none;
    border-radius: 0;
}
body.isMac:not(.card) .spin-box:focus-within {
    outline: 2px solid var(--mac-accent);
    outline-offset: 2px;
}
body.isMac:not(.card) :is(.card, .modal-content, .popover, .dropdown-menu) {
    --bs-card-bg: var(--mac-surface);
    --bs-card-border-color: var(--mac-border);
    --bs-modal-bg: var(--mac-surface);
    --bs-modal-color: var(--mac-text);
    --bs-dropdown-bg: var(--mac-surface);
    --bs-dropdown-color: var(--mac-text);
    --bs-dropdown-link-color: var(--mac-text);
    --bs-dropdown-link-hover-bg: var(--mac-selection);
    border-radius: 10px;
    border-color: var(--mac-border);
}
body.isMac:not(.card) .nav-tabs { border-color: var(--mac-border); }
body.isMac:not(.card) .nav-tabs .nav-link {
    border-radius: 7px 7px 0 0;
    color: var(--mac-secondary);
}
body.isMac:not(.card) .nav-tabs .nav-link.active {
    color: var(--mac-text);
    background: var(--mac-surface);
    border-color: var(--mac-border);
}
body.isMac:not(.card) .dropdown-item:hover {
    color: var(--mac-text);
    background: var(--mac-selection);
}
body.isMac:not(.card) :is(.graphs-container, .deck-options-page) .container {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    border-color: var(--mac-border);
    border-radius: 12px;
}
body.isMac:not(.card) :is(.graphs-container, .deck-options-page) h1 {
    font-size: 22px;
    font-weight: 650;
    letter-spacing: -0.3px;
    padding-bottom: 12px;
}
body.isMac:not(.card) .editor-toolbar {
    padding: 6px 0 10px;
    border-color: var(--mac-border);
}
body.isMac:not(.card) .editor-toolbar :is(button, .linkb) {
    border: 1px solid transparent;
    border-radius: 6px;
    background: transparent;
    box-shadow: none;
}
body.isMac:not(.card) .editor-toolbar :is(button, .linkb):hover {
    background: var(--mac-hover);
}
body.isMac:not(.card) .editor-toolbar :is(button, .linkb).active {
    background: var(--mac-selection);
    color: var(--mac-accent);
}
body.isMac:not(.card) .field-container {
    margin-block: 8px;
    border-radius: 9px;
}
body.isMac:not(.card) .editor-field {
    border: 1px solid var(--mac-border);
    border-radius: 9px;
    box-shadow: none;
}
body.isMac:not(.card) .editor-field:focus-within {
    outline: 2px solid var(--mac-accent);
    outline-offset: -2px;
}
body.isMac:not(.card) .editor-field.dupe,
body.isMac:not(.card) .editor-field.dupe:focus-within {
    outline-color: var(--accent-danger);
}
body.isMac:not(.card) :is(button, input, select):disabled { opacity: 0.55; }
@media (prefers-reduced-motion: reduce) {
    body.isMac:not(.card) :is(button, .btn) { transition: none; }
}
"""
