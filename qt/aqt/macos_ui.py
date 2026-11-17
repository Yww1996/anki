# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Shared macOS appearance for native widgets and embedded application pages."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aqt.qt import QTabWidget


def widget_styles(night: bool, down_icon: str, up_icon: str) -> str:
    if night:
        canvas, surface, text = "#151820", "#1d222d", "#e1e6ef"
        secondary, border, hover = "#8994a8", "#2b3240", "#29334e"
        selection, accent = "#2a3555", "#8196f4"
    else:
        canvas, surface, text = "#fbfcfe", "#ffffff", "#252b38"
        secondary, border, hover = "#6b7585", "#e9ecf2", "#f0f3f9"
        selection, accent = "#eef2fc", "#4663d8"

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
QDialogButtonBox QPushButton:default {{ background-color: {accent}; color: {"#151a2a" if night else "#ffffff"}; }}
QDialogButtonBox QPushButton:default:hover {{ background-color: {"#95a6ff" if night else "#3e57c2"}; }}
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
    --mac-background: #fbfcfe;
    --mac-surface: #ffffff;
    --mac-text: #252b38;
    --mac-secondary: #6b7585;
    --mac-border: #e9ecf2;
    --mac-hover: #f0f3f9;
    --mac-selection: #eef2fc;
    --mac-accent: #4663d8;
    --mac-accent-contrast: #ffffff;
    --mac-accent-hover: #3e57c2;
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
    --mac-background: #151820;
    --mac-surface: #1d222d;
    --mac-text: #e1e6ef;
    --mac-secondary: #8994a8;
    --mac-border: #2b3240;
    --mac-hover: #29334e;
    --mac-selection: #2a3555;
    --mac-accent: #8196f4;
    --mac-accent-contrast: #151a2a;
    --mac-accent-hover: #95a6ff;
}
body.isMac:not(.card) :is(button, input, select) { font-family: inherit; }
body.isMac:not(.card) :is(button, .btn) {
    border-radius: 7px;
    box-shadow: none;
    font-weight: 500;
    transition-duration: 0.1s;
}
body.isMac:not(.card) button:not(.btn, .btn-close, .icon-button, .item-card) {
    background: var(--mac-surface);
    color: var(--mac-text);
    border-color: var(--mac-border);
}
body.isMac:not(.card) button:not(.btn, .btn-close, .icon-button, .item-card):hover {
    background: var(--mac-hover);
}
body.isMac:not(.card) :is(.btn-primary, .btn-primary:hover) {
    --bs-btn-bg: var(--mac-accent);
    --bs-btn-border-color: var(--mac-accent);
    --bs-btn-hover-bg: var(--mac-accent-hover);
    --bs-btn-hover-border-color: var(--mac-accent-hover);
    --bs-btn-active-bg: var(--mac-accent-hover);
    --bs-btn-color: var(--mac-accent-contrast);
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


def modern_progress_styles(night: bool) -> str:
    """Match progress sheets to the Svelte shell without changing cancellation."""
    if night:
        surface, text, muted, border, accent = (
            "#1d222d",
            "#e1e6ef",
            "#8994a8",
            "#2b3240",
            "#8196f4",
        )
    else:
        surface, text, muted, border, accent = (
            "#ffffff",
            "#252c3d",
            "#6b7585",
            "#e9ecf2",
            "#465fd9",
        )
    return f"""
QDialog {{ background: {surface}; color: {text}; }}
QLabel {{ color: {text}; font-size: 13px; }}
QPushButton {{ min-height: 26px; padding: 4px 16px; border: 1px solid {border};
    border-radius: 7px; background: {surface}; color: {text}; }}
QProgressBar {{ border: none; border-radius: 3px; min-height: 6px;
    max-height: 6px; background: {border}; color: {muted}; }}
QProgressBar::chunk {{ background: {accent}; border-radius: 3px; }}
"""


def notification_styles(night: bool) -> str:
    if night:
        surface, text, border = "#232938", "#e1e6ef", "#2b3240"
        success, tint, muted, hover = "#7cc9a2", "#243f37", "#8994a8", "#30394b"
    else:
        surface, text, border = "#ffffff", "#252b38", "#e9ecf2"
        success, tint, muted, hover = "#218566", "#e9f5ee", "#6b7585", "#f0f3f9"
    return f"""
QFrame#modernSyncNotice {{ background: {surface}; border: 1px solid {border}; border-radius: 11px; }}
QFrame#modernSyncNotice QLabel {{ color: {text}; background: transparent; border: none; font-size: 13px; }}
QFrame#modernSyncNotice QLabel#noticeIcon {{ color: {success}; background: {tint}; border-radius: 12px; font-size: 17px; }}
QFrame#modernSyncNotice QPushButton#noticeClose {{ min-height: 0; min-width: 0; padding: 0; border: none; border-radius: 6px; color: {muted}; background: transparent; font-size: 18px; }}
QFrame#modernSyncNotice QPushButton#noticeClose:hover {{ background: {hover}; color: {text}; }}
"""
