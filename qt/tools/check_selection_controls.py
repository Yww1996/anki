# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Check expanded selection controls in real Qt webviews with private test data."""

import json

from check_modern_ui_regressions import RegressionChecks, run
from PyQt6.QtTest import QTest

import aqt
from aqt.preferences import Preferences
from aqt.qt import Qt
from aqt.theme import Theme, theme_manager


class SelectionChecks(RegressionChecks):
    def start(self):
        if not aqt.mw.col or aqt.mw._background_op_count:
            self.later(self.start)
            return
        self.dark = False
        self.theme()

    def theme(self):
        aqt.mw.resize(400, 740)
        aqt.mw.pm.set_theme(Theme.DARK if self.dark else Theme.LIGHT)
        theme_manager.apply_style()
        aqt.mw.moveToState("deckBrowser")
        self.later(self.open, 700)

    def open(self):
        self.web = aqt.mw.web
        self.web.eval(
            "window.beforeKeyboardDeck=document.querySelector('.split-focus h1').textContent;document.querySelector('.split-mobile-picker button').click()"
        )
        self.later(self.popup)

    def popup(self):
        self.snapshot("deck-open-" + ("dark" if self.dark else "light"))
        self.evaluate(
            self.web,
            "expanded deck list uses themed surface and fits viewport",
            "(()=>{const p=document.querySelector('.modern-select-content');const r=p.getBoundingClientRect();const probe=document.createElement('span');probe.style.background='var(--popover)';document.body.append(probe);const expected=getComputedStyle(probe).backgroundColor;probe.remove();return getComputedStyle(p).backgroundColor===expected&&r.left>=0&&r.right<=innerWidth+.5&&r.bottom<=innerHeight+.5&&!!p.querySelector('[aria-selected=true] .modern-select-check svg')&&!document.querySelector('select');})()",
            self.keyboard,
        )

    def keyboard(self):
        self.web.setFocus()
        for key in (Qt.Key.Key_End, Qt.Key.Key_Return):
            QTest.keyClick(self.web.focusProxy(), key)
            QTest.qWait(30)
        self.later(self.selected)

    def selected(self):
        self.evaluate(
            self.web,
            "native keyboard selects a deck and closes the list",
            "!document.querySelector('.modern-select-content')&&document.querySelector('.split-mobile-picker button span').textContent===document.querySelector('.split-focus h1').textContent&&document.querySelector('.split-focus h1').textContent!==window.beforeKeyboardDeck",
            self.escape_open,
        )

    def escape_open(self):
        self.web.eval("document.querySelector('.split-mobile-picker button').click()")
        self.later(self.escape)

    def escape(self):
        QTest.keyClick(self.web.focusProxy(), Qt.Key.Key_Escape)
        self.later(self.escaped)

    def escaped(self):
        self.evaluate(
            self.web,
            "Escape closes list and restores trigger focus",
            "!document.querySelector('.modern-select-content')&&document.activeElement===document.querySelector('.split-mobile-picker button')",
            self.preferences_open,
        )

    def preferences_open(self):
        self.preferences = Preferences(aqt.mw)
        self.later(self.preferences_ready, 700)

    def preferences_ready(self):
        self.web = self.preferences.modern_preferences.web
        self.web.eval(
            "document.querySelector('.modern-select-trigger:not(:disabled)').click()"
        )
        self.later(self.preferences_popup)

    def preferences_popup(self):
        self.preferences.grab().save(
            str(
                self.artifacts
                / (
                    "preferences-open-dark.png"
                    if self.dark
                    else "preferences-open-light.png"
                )
            )
        )
        self.evaluate(
            self.web,
            "settings dropdown uses the same shared list and avoids native select",
            "!!document.querySelector('.modern-select-content .modern-select-option')&&!document.querySelector('select')",
            self.preferences_close,
        )

    def preferences_close(self):
        self.web.setFocus()
        QTest.keyClick(self.web.focusProxy(), Qt.Key.Key_Escape)
        schema = self.preferences.modern_preferences.schema()
        self.target = self.preferences.form.useCurrent
        self.expected_index = 1 - self.target.currentIndex()
        controls = self.preferences.modern_preferences.controls
        self.target_id = next(
            key for key, widget in controls.items() if widget is self.target
        )
        page_id = next(
            page["id"]
            for page in schema["pages"]
            if any(
                item["id"] == self.target_id
                for group in page["groups"]
                for item in group["items"]
            )
        )
        self.web.eval(
            f"document.querySelectorAll('.preferences-nav nav button')[{page_id}].click()"
        )
        self.later(self.preference_edit)

    def preference_edit(self):
        self.check(
            "Escape dismisses settings popup without closing settings",
            self.preferences.isVisible(),
        )
        self.web.eval(f"document.getElementById('{self.target_id}').click()")
        self.later(self.preference_choose)

    def preference_choose(self):
        self.web.setFocus()
        QTest.keyClick(
            self.web.focusProxy(),
            Qt.Key.Key_Home if self.expected_index == 0 else Qt.Key.Key_End,
        )
        QTest.qWait(30)
        QTest.keyClick(self.web.focusProxy(), Qt.Key.Key_Return)
        self.later(self.preference_changed)

    def preference_changed(self):
        self.check(
            "select change reaches the original numeric preference",
            self.target.currentIndex() == self.expected_index,
        )
        self.evaluate(
            self.web,
            "selected setting label matches native value",
            f"document.getElementById('{self.target_id}').textContent.trim()==={json.dumps(self.target.currentText())}",
            lambda: self.preferences.accept_with_callback(self.cards_open),
        )

    def cards_open(self):
        self.check(
            "select preference is persisted",
            aqt.mw.col.get_preferences().editing.adding_defaults_to_current_deck
            == (self.expected_index == 0),
        )
        aqt.mw.web.eval("document.querySelector('.quick-search-button').click()")
        self.later(self.cards_ready, 700)

    def cards_ready(self):
        self.web = aqt.mw.web
        self.web.eval("document.querySelector('.live-deck-filter').click()")
        self.later(self.cards_popup)

    def cards_popup(self):
        self.snapshot("filter-open-" + ("dark" if self.dark else "light"))
        self.evaluate(
            self.web,
            "card filter uses shared styled options",
            "!!document.querySelector('.modern-select-option[data-value=all]')&&!document.querySelector('select')",
            self.next,
        )

    def next(self):
        QTest.keyClick(self.web.focusProxy(), Qt.Key.Key_Escape)
        if self.dark:
            self.finish(True)
        else:
            self.dark = True
            aqt.mw.deckBrowser.modern_ui.active_page = "home"
            self.theme()


if __name__ == "__main__":
    raise SystemExit(run(SelectionChecks))
