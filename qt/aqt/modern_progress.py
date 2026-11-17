# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Progress painting independent of backend status polling."""

from __future__ import annotations

import math
import time

from aqt.qt import (
    QColor,
    QHideEvent,
    QPainter,
    QPaintEvent,
    QProgressBar,
    QRectF,
    QShowEvent,
    Qt,
    QTimer,
    qconnect,
)
from aqt.theme import theme_manager


class SmoothProgressBar(QProgressBar):
    def __init__(self, old: QProgressBar, reduced_motion: bool) -> None:
        super().__init__(old.parentWidget())
        self.setObjectName(old.objectName())
        self.setAccessibleName(old.accessibleName() or "进度")
        self.setRange(old.minimum(), old.maximum())
        self.setValue(old.value())
        self.setFixedHeight(6)
        self.reduced_motion = reduced_motion
        self.started = time.monotonic()
        self.displayed = 0.0
        self.previous = 0.0
        self.target = 0.0
        self.changed = self.started
        self.frame_timer = QTimer(self)
        self.frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.frame_timer.setInterval(16)
        qconnect(self.frame_timer.timeout, self._frame)
        qconnect(self.valueChanged, self._value_changed)
        self._value_changed(self.value())

    def _value_changed(self, value: int) -> None:
        self.previous = self.displayed
        self.target = max(
            0.0,
            min(
                1.0, (value - self.minimum()) / max(1, self.maximum() - self.minimum())
            ),
        )
        self.changed = time.monotonic()
        if self.reduced_motion or self.target < self.displayed:
            self.displayed = self.target
        elif self.isVisible() and not self.frame_timer.isActive():
            self.frame_timer.start()
        self.update()

    def _frame(self) -> None:
        if self.maximum() != 0:
            elapsed = min(1.0, (time.monotonic() - self.changed) / 0.15)
            self.displayed = self.previous + (self.target - self.previous) * (
                1 - (1 - elapsed) ** 3
            )
            if elapsed >= 1:
                self.frame_timer.stop()
        self.update()

    def showEvent(self, event: QShowEvent | None) -> None:
        super().showEvent(event)
        if not self.reduced_motion:
            self.frame_timer.start()

    def hideEvent(self, event: QHideEvent | None) -> None:
        self.frame_timer.stop()
        super().hideEvent(event)

    def setMaximum(self, maximum: int) -> None:
        super().setMaximum(maximum)
        if not hasattr(self, "frame_timer"):
            return
        if maximum == 0 and self.isVisible() and not self.reduced_motion:
            self.frame_timer.start()

    def paintEvent(self, event: QPaintEvent | None) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        night = theme_manager.night_mode
        painter.setBrush(QColor("#2b3240" if night else "#e9ecf2"))
        painter.drawRoundedRect(QRectF(self.rect()), 3, 3)
        painter.setBrush(QColor("#8196f4" if night else "#4663d8"))
        if self.maximum() == 0:
            width = self.width() * 0.28
            # Reduced motion uses a stationary indicator rather than a slow, stepped animation.
            phase = (
                0.5
                if self.reduced_motion
                else (1 - math.cos((time.monotonic() - self.started) * math.tau / 1.6))
                / 2
            )
            left = (self.width() - width) * phase
            painter.drawRoundedRect(QRectF(left, 0, width, self.height()), 3, 3)
        else:
            painter.drawRoundedRect(
                QRectF(0, 0, self.width() * self.displayed, self.height()), 3, 3
            )
