# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Match the main window's native title bar to the application canvas."""

from __future__ import annotations

import ctypes
from functools import lru_cache

from aqt import gui_hooks
from aqt.qt import QEvent, QObject, QTimer, QWidget
from aqt.theme import theme_manager


@lru_cache(maxsize=1)
def _runtime():
    runtime = ctypes.CDLL("/usr/lib/libobjc.A.dylib")
    runtime.sel_registerName.argtypes = [ctypes.c_char_p]
    runtime.sel_registerName.restype = ctypes.c_void_p
    runtime.objc_getClass.argtypes = [ctypes.c_char_p]
    runtime.objc_getClass.restype = ctypes.c_void_p
    return runtime


def _send(receiver, selector: str, restype, argtypes=(), args=()):
    # objc_msgSend must have a separate, exact ABI signature for each call.
    runtime = _runtime()
    function = ctypes.CFUNCTYPE(restype, ctypes.c_void_p, ctypes.c_void_p, *argtypes)(
        ("objc_msgSend", runtime)
    )
    return function(receiver, runtime.sel_registerName(selector.encode()), *args)


def native_window(widget: QWidget):
    # QWidget.winId() is an NSView on Cocoa, not an NSWindow.
    return _send(int(widget.winId()), "window", ctypes.c_void_p)


def apply_titlebar(widget: QWidget) -> None:
    window = native_window(widget)
    if not window:
        return
    runtime = _runtime()
    color_class = runtime.objc_getClass(b"NSColor")
    rgb = (21, 24, 32) if theme_manager.night_mode else (251, 252, 254)
    color = _send(
        color_class,
        "colorWithSRGBRed:green:blue:alpha:",
        ctypes.c_void_p,
        (ctypes.c_double,) * 4,
        (*[value / 255 for value in rgb], 1.0),
    )
    _send(window, "setBackgroundColor:", None, (ctypes.c_void_p,), (color,))
    _send(window, "setTitlebarAppearsTransparent:", None, (ctypes.c_bool,), (True,))
    selector = runtime.sel_registerName(b"setTitlebarSeparatorStyle:")
    if _send(
        window, "respondsToSelector:", ctypes.c_bool, (ctypes.c_void_p,), (selector,)
    ):
        # NSTitlebarSeparatorStyleNone. Keep the standard title and window buttons.
        _send(window, "setTitlebarSeparatorStyle:", None, (ctypes.c_long,), (1,))


class MainWindowTitlebar(QObject):
    def __init__(self, window: QWidget) -> None:
        super().__init__(window)
        self.window = window
        window.installEventFilter(self)
        gui_hooks.theme_did_change.append(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        # Apply after Qt has created/restored its Cocoa window and palette.
        QTimer.singleShot(0, self.apply)

    def apply(self) -> None:
        if self.window.isVisible():
            apply_titlebar(self.window)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.Show, QEvent.Type.WindowStateChange):
            self.refresh()
        return False
