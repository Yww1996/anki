# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Svelte presentation of upstream preference controls and their existing signals."""

from __future__ import annotations

import json
from typing import Any

from aqt.qt import (
    QAbstractButton,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from aqt.theme import theme_manager
from aqt.webview import AnkiWebView


class ModernPreferences:
    uses_modern_ui = True

    def __init__(self, dialog: Any) -> None:
        self.dialog = dialog
        self.controls: dict[str, QWidget] = {}
        self.pages = [
            dialog.form.tabWidget.widget(i)
            for i in range(dialog.form.tabWidget.count())
        ]
        self.titles = [
            dialog.form.tabWidget.tabText(i)
            for i in range(dialog.form.tabWidget.count())
        ]
        self.web = AnkiWebView(dialog)
        self.web.set_bridge_command(self.handle, self)
        layout = dialog.layout()
        while layout.count():
            item = layout.takeAt(0)
            if widget := item.widget():
                widget.hide()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.web)
        dialog.setMinimumSize(740, 540)
        dialog.resize(960, 720)
        self.web.stdHtml(
            '<div id="app" data-mode="preferences"></div>'
            + self.web.bundledScript("modern/modern.js"),
            css=["modern/modern.css"],
            js=[],
            default_css=False,
            context=self,
        )

    def label(self, widget: QWidget) -> str:
        for label in self.dialog.findChildren(QLabel):
            if label.buddy() is widget:
                return label.text().replace("&", "")
        parent = widget.parentWidget()
        if parent and (layout := parent.layout()):
            if isinstance(layout, QFormLayout):
                label = layout.labelForField(widget)
                if isinstance(label, QLabel):
                    return label.text().replace("&", "")
            if isinstance(layout, QGridLayout):
                index = layout.indexOf(widget)
                if index >= 0:
                    row, column, _, _ = layout.getItemPosition(index)
                    for col in range(column):
                        item = layout.itemAtPosition(row, col)
                        if item and isinstance(label := item.widget(), QLabel):
                            return label.text().replace("&", "")
        return widget.accessibleName() or widget.toolTip() or "选项"

    def schema(self) -> dict[str, Any]:
        self.controls.clear()
        pages = []
        for index, page in enumerate(self.pages):
            groups: list[dict[str, Any]] = []
            self._walk(page, groups, {"title": "", "items": []})
            # Labs keeps its upstream Svelte implementation and API in a separate sheet.
            pages.append(
                {
                    "id": str(index),
                    "title": self.titles[index].replace("&", ""),
                    "groups": groups,
                    "labs": page is self.dialog.form.labsTab
                    or (
                        isinstance(page, QScrollArea)
                        and page.widget() is self.dialog.form.labsTab
                    ),
                }
            )
        return {"pages": pages, "dark": theme_manager.night_mode}

    def _walk(self, widget: QWidget, groups: list, group: dict) -> None:
        if isinstance(widget, QScrollArea):
            if widget.widget():
                self._walk(widget.widget(), groups, group)
            return
        if isinstance(widget, QGroupBox):
            group = {"title": widget.title().replace("&", ""), "items": []}
            groups.append(group)
        layout = widget.layout()
        if not layout:
            return

        def visit(layout: Any) -> None:
            for index in range(layout.count()):
                item = layout.itemAt(index)
                if item.layout():
                    visit(item.layout())
                elif child := item.widget():
                    if isinstance(child, (QGroupBox, QScrollArea)):
                        self._walk(child, groups, group)
                    elif isinstance(
                        child,
                        (
                            QCheckBox,
                            QComboBox,
                            QSpinBox,
                            QDoubleSpinBox,
                            QLineEdit,
                            QAbstractButton,
                        ),
                    ):
                        key = f"control-{len(self.controls)}"
                        self.controls[key] = child
                        entry = {
                            "id": key,
                            "label": self.label(child),
                            "disabled": not child.isEnabled(),
                            "hidden": child.isHidden(),
                            "hint": child.toolTip(),
                        }
                        if isinstance(child, QCheckBox):
                            entry.update(
                                type="switch",
                                label=child.text().replace("&", ""),
                                value=child.isChecked(),
                            )
                        elif isinstance(child, QComboBox):
                            entry.update(
                                type="select",
                                value=child.currentIndex(),
                                options=[
                                    {"label": child.itemText(i), "value": i}
                                    for i in range(child.count())
                                ],
                            )
                        elif isinstance(child, (QSpinBox, QDoubleSpinBox)):
                            entry.update(
                                type="number",
                                value=child.value(),
                                min=child.minimum(),
                                max=child.maximum(),
                                step=child.singleStep(),
                                suffix=child.suffix(),
                            )
                        elif isinstance(child, QLineEdit):
                            entry.update(
                                type="text",
                                value=child.text(),
                                placeholder=child.placeholderText(),
                            )
                        else:
                            entry.update(
                                type="button", label=child.text().replace("&", "")
                            )
                        if group not in groups:
                            groups.append(group)
                        group["items"].append(entry)
                    elif isinstance(child, QLabel):
                        if child.objectName() in (
                            "syncUser",
                            "syncAnkiHubUser",
                            "backup_explanation",
                        ):
                            if group not in groups:
                                groups.append(group)
                            group["items"].append(
                                {
                                    "type": "info",
                                    "label": child.text(),
                                    "id": child.objectName(),
                                    "hidden": child.isHidden(),
                                }
                            )
                    elif not isinstance(child, AnkiWebView):
                        self._walk(child, groups, group)

        visit(layout)

    def handle(self, raw: str) -> Any:
        if not raw.startswith("prefs:"):
            return None
        request = json.loads(raw[len("prefs:") :])
        action = request.get("action")
        if action == "load":
            return self.schema()
        if action == "done":
            self.dialog.accept()
            return None
        if action == "help":
            self.dialog.form.buttonBox.helpRequested.emit()
            return None
        if action == "labs":
            self.show_labs()
            return None
        widget = self.controls.get(request.get("id"))
        if widget is None or not widget.isEnabled() or widget.isHidden():
            return self.schema()
        value = request.get("value")
        if action in ("change", "edit"):
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QComboBox):
                if 0 <= int(value) < widget.count():
                    widget.setCurrentIndex(int(value))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))
        elif action == "button" and isinstance(widget, QAbstractButton):
            widget.click()
        if action == "edit":
            current: str | int | float
            if isinstance(widget, QLineEdit):
                current = widget.text()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                current = widget.value()
            else:
                return None
            return {"id": request["id"], "value": current}
        return self.schema()

    def show_labs(self) -> None:
        page = self.dialog.form.labsTab
        original_parent = page.parentWidget()
        original_scroll = original_parent.parentWidget() if original_parent else None
        original_layout = original_parent.layout() if original_parent else None
        if isinstance(original_scroll, QScrollArea):
            original_scroll.takeWidget()
        sheet = QDialog(self.dialog)
        sheet.setWindowTitle(self.titles[-1])
        sheet.resize(760, 600)
        QVBoxLayout(sheet).addWidget(page)
        page.show()
        sheet.exec()
        if isinstance(original_scroll, QScrollArea):
            original_scroll.setWidget(page)
        else:
            page.setParent(original_parent)
        if original_layout:
            original_layout.addWidget(page)
        page.hide()
        sheet.deleteLater()
