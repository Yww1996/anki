# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Check native title-bar appearance in a private synthetic profile copy."""

from __future__ import annotations

import ctypes
import subprocess

from check_modern_ui_regressions import RegressionChecks, run

import aqt
from aqt.macos_window import _send, native_window
from aqt.theme import Theme, theme_manager


class TitlebarChecks(RegressionChecks):
    def start(self):
        if not aqt.mw.col or aqt.mw._background_op_count:
            self.later(self.start)
            return
        aqt.mw.resize(900, 700)
        self.dark = False
        self.change_theme()

    def change_theme(self):
        aqt.mw.pm.set_theme(Theme.DARK if self.dark else Theme.LIGHT)
        theme_manager.apply_style()
        aqt.mw.deckBrowser.modern_ui.active_page = "home"
        aqt.mw.moveToState("deckBrowser")
        self.later(self.verify, 900)

    def verify(self):
        name = "dark" if self.dark else "light"
        window = native_window(aqt.mw)
        self.check(name + ": native window exists", bool(window))
        self.check(
            name + ": title-bar material is transparent",
            _send(window, "titlebarAppearsTransparent", ctypes.c_bool),
        )
        self.check(
            name + ": title-bar separator is removed",
            _send(window, "titlebarSeparatorStyle", ctypes.c_long) == 1,
        )
        color = _send(window, "backgroundColor", ctypes.c_void_p)
        actual = [
            _send(color, channel + "Component", ctypes.c_double)
            for channel in ("red", "green", "blue")
        ]
        expected = (21, 24, 32) if self.dark else (251, 252, 254)
        self.check(
            name + ": native canvas matches web canvas",
            all(abs(a - b / 255) < 0.001 for a, b in zip(actual, expected)),
        )
        mask = _send(window, "styleMask", ctypes.c_ulong)
        self.check(
            name + ": native title, close, minimize and resize remain enabled",
            mask & 15 == 15,
        )
        self.check(
            name + ": web content does not extend under the window buttons",
            not mask & (1 << 15),
        )
        for index in (0, 1, 2):
            button = _send(
                window,
                "standardWindowButton:",
                ctypes.c_void_p,
                (ctypes.c_ulong,),
                (index,),
            )
            self.check(
                name + f": standard window button {index} is visible",
                bool(button) and not _send(button, "isHidden", ctypes.c_bool),
            )
        number = _send(window, "windowNumber", ctypes.c_long)
        subprocess.run(
            [
                "screencapture",
                "-x",
                "-l",
                str(number),
                str(self.artifacts / f"titlebar-{name}.png"),
            ],
            check=True,
        )
        if self.dark:
            self.finish(True)
        else:
            self.dark = True
            self.change_theme()


if __name__ == "__main__":
    raise SystemExit(run(TitlebarChecks))
