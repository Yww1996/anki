# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Check the readable, compact home in a private synthetic profile copy."""

from __future__ import annotations

from check_modern_ui_regressions import RegressionChecks, run

import aqt
from aqt.theme import Theme, theme_manager


class ReadabilityChecks(RegressionChecks):
    def start(self):
        if not aqt.mw.col or aqt.mw._background_op_count:
            self.later(self.start)
            return
        self.sizes = [(1200, 800, False), (900, 650, False), (400, 740, True)]
        self.index = 0
        self.next_size()

    def next_size(self):
        width, height, dark = self.sizes[self.index]
        self.name = f"{width}-{height}-" + ("dark" if dark else "light")
        aqt.mw.resize(width, height)
        aqt.mw.pm.set_theme(Theme.DARK if dark else Theme.LIGHT)
        theme_manager.apply_style()
        aqt.mw.deckBrowser.modern_ui.active_page = "home"
        aqt.mw.moveToState("deckBrowser")
        self.later(self.home, 800)

    def home(self):
        self.snapshot("home-" + self.name)
        self.evaluate(
            aqt.mw.web,
            self.name + ": simple home, no duplicate deck table or secondary panels",
            """!!document.querySelector('.native-split-page .split-study-action') && !document.querySelector('.deck-table,.home-aside,.study-hero,.memory-art,.activity-panel,.sidebar-tip')""",
            self.fonts,
        )

    def fonts(self):
        self.evaluate(
            aqt.mw.web,
            self.name + ": body, primary action and deck labels use readable sizes",
            """(()=>{
            const size=selector=>parseFloat(getComputedStyle(document.querySelector(selector)).fontSize);
            return size('body')>=16 && size('.split-study-action')>=15 && size('.split-focus h1')>=24 && size('.split-counts span')>=14 && (!document.querySelector('.main-nav-button') || size('.main-nav-button')>=15);
        })()""",
            self.layout,
        )

    def layout(self):
        self.evaluate(
            aqt.mw.web,
            self.name + ": study action and queue counts are visible without scrolling",
            """(()=>{
            const visible=element=>{const r=element.getBoundingClientRect();return r.left>=0 && r.right<=innerWidth+.5 && r.top>=0 && r.bottom<=innerHeight+.5;};
            return visible(document.querySelector('.split-study-action')) && visible(document.querySelector('.split-counts')) && visible(document.querySelector('.split-focus h1'));
        })()""",
            self.actions,
        )

    def actions(self):
        self.evaluate(
            aqt.mw.web,
            self.name + ": header actions stay inside the viewport",
            """[...document.querySelectorAll('.app-topbar button,.native-split-page button')].filter(b=>b.getClientRects().length && b.getBoundingClientRect().top<innerHeight).every(b=>{const r=b.getBoundingClientRect();return r.left>=-.5&&r.right<=innerWidth+.5;})""",
            self.advance,
        )

    def advance(self):
        self.index += 1
        if self.index < len(self.sizes):
            self.next_size()
        else:
            self.finish(True)


if __name__ == "__main__":
    raise SystemExit(run(ReadabilityChecks))
