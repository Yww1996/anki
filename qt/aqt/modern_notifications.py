# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Native notices that survive embedded-page refreshes without taking focus."""

from __future__ import annotations

from typing import Any

from aqt import gui_hooks
from aqt.qt import (
    QColor,
    QEvent,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    Qt,
    QTimer,
    QWidget,
    qconnect,
    sip,
)
from aqt.theme import theme_manager
from aqt.utils import tr


class SyncCompleteNotice(QFrame):
    def __init__(self, parent: QWidget, message: str, period: int) -> None:
        super().__init__(parent)
        self.owner = parent
        self.dismissed = False
        self.setObjectName("modernSyncNotice")
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName(message)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 12, 12)
        layout.setSpacing(10)
        self.icon = QLabel("✓", self)
        self.icon.setObjectName("noticeIcon")
        self.icon.setFixedSize(25, 25)
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message = QLabel(message, self)
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setWordWrap(True)
        self.close_button = QPushButton("×", self)
        self.close_button.setObjectName("noticeClose")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_button.setAccessibleName(tr.actions_close())
        self.close_button.setToolTip(tr.actions_close())
        qconnect(self.close_button.clicked, self.dismiss)
        layout.addWidget(self.icon)
        layout.addWidget(self.message, 1)
        layout.addWidget(self.close_button)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 28))
        self.setGraphicsEffect(shadow)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        qconnect(self.timer.timeout, self.dismiss)
        self.owner.installEventFilter(self)
        gui_hooks.theme_did_change.append(self.apply_theme)
        self.apply_theme()
        self.reposition()
        self.show()
        self.raise_()
        self.timer.start(period)

    def apply_theme(self) -> None:
        from aqt.macos_ui import notification_styles

        self.setStyleSheet(notification_styles(theme_manager.night_mode))

    def reposition(self) -> None:
        available = max(1, self.owner.width() - 32)
        self.setFixedWidth(min(380, available, max(240, self.sizeHint().width())))
        self.adjustSize()
        self.move(
            max(0, self.owner.width() - self.width() - 16),
            max(0, self.owner.height() - self.height() - 24),
        )

    def eventFilter(self, obj: Any, event: QEvent) -> bool:
        if obj is self.owner and not self.dismissed:
            if event.type() == QEvent.Type.Resize:
                self.reposition()
            elif event.type() in (QEvent.Type.Hide, QEvent.Type.Close):
                self.dismiss()
        return super().eventFilter(obj, event)

    def dismiss(self) -> None:
        if self.dismissed:
            return
        self.dismissed = True
        self.timer.stop()
        self.owner.removeEventFilter(self)
        gui_hooks.theme_did_change.remove(self.apply_theme)
        self.hide()
        self.deleteLater()


def show_collection_sync_complete(mw: Any, period: int = 3000) -> SyncCompleteNotice:
    previous = getattr(mw, "_modern_sync_notice", None)
    if previous is not None and not sip.isdeleted(previous):
        previous.dismiss()
    notice = SyncCompleteNotice(mw, tr.sync_collection_complete(), period)
    mw._modern_sync_notice = notice
    return notice
