# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Exercise the macOS UI using a private copy of a synthetic profile.

Run with the built Anki Python/runtime packages on PYTHONPATH. The fixture is
never opened by Anki: its copy is stripped of sync credentials before startup.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import traceback
import uuid
from pathlib import Path

os.environ["ANKI_SINGLE_INSTANCE_KEY"] = "modern-ui-regressions-" + uuid.uuid4().hex

import aqt
from aqt import gui_hooks
from aqt.preferences import Preferences
from aqt.profiles import ProfileManager
from aqt.qt import QTimer
from aqt.theme import Theme, theme_manager


def run(check_type=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-base", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    options = parser.parse_args()
    options.artifacts.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="anki-ui-regressions-") as temporary:
        base = Path(temporary) / "profile"
        shutil.copytree(options.fixture_base, base)
        manager = ProfileManager(base)
        manager.setupMeta()
        assert options.profile in manager.profiles(), (
            "Use an existing synthetic fixture profile"
        )
        for name in manager.profiles():
            manager.load(name)
            manager.profile.update(
                syncKey=None, syncUser="", autoSync=False, autoSyncMediaMinutes=0
            )
            manager.save()
        manager.db.close()
        app = aqt._run(
            [
                "anki-ui-regressions",
                "-b",
                str(base),
                "-p",
                options.profile,
                "-l",
                "zh_CN",
                "--safemode",
            ],
            exec=False,
        )
        assert app is not None, "The test must run in its own instance"
        tests = (check_type or RegressionChecks)(app, options.artifacts)
        QTimer.singleShot(500, tests.start)
        QTimer.singleShot(90000, tests.timeout)
        app.exec()
        return 0 if tests.finished and tests.passed else 1


class RegressionChecks:
    def __init__(self, app, artifacts: Path) -> None:
        self.app = app
        self.artifacts = artifacts
        self.checks = []
        self.finished = False
        self.passed = False
        self.hooks = []
        self.flags = dict(
            deck_will=0,
            deck_did=0,
            overview_will=0,
            bottom=0,
            deck_click=0,
            content_click=0,
            bottom_click=0,
        )

    def check(self, name, result) -> None:
        self.checks.append({"name": name, "passed": bool(result)})
        print(("PASS " if result else "FAIL ") + name, flush=True)
        assert result, name

    def later(self, function, delay=200):
        def guarded():
            if self.finished:
                return
            try:
                function()
            except Exception:
                traceback.print_exc()
                self.finish(False)

        QTimer.singleShot(delay, guarded)

    def evaluate(self, web, name, javascript, next_step):
        def received(value):
            try:
                self.check(name, value is True)
                self.later(next_step)
            except Exception:
                traceback.print_exc()
                self.finish(False)

        web.evalWithCallback(javascript, received)

    def snapshot(self, name):
        aqt.mw.grab().save(str(self.artifacts / (name + ".png")))

    def start(self):
        mw = aqt.mw
        if not mw.col or mw._background_op_count:
            self.later(self.start)
            return
        try:
            mw.pm.set_theme(Theme.LIGHT)
            theme_manager.apply_style()
            mw.resize(1200, 800)
            col = mw.col
            self.parent = col.decks.id('Regression * "parent"')
            child = col.decks.id('Regression * "parent"::Child')
            grandchild = col.decks.id('Regression * "parent"::Child::Grandchild')
            other = col.decks.id("Regression unrelated")
            model = next(
                model
                for model in col.models.all()
                if model["type"] == 0 and len(model["flds"]) >= 2
            )
            self.expected = set()
            for deck_id, count in (
                (self.parent, 2),
                (child, 3),
                (grandchild, 1),
                (other, 1),
            ):
                for index in range(count):
                    note = col.new_note(model)
                    note.fields[0] = f"UI regression {deck_id} {index}"
                    note.fields[1] = "Synthetic answer"
                    col.add_note(note, deck_id)
                    if deck_id != other:
                        self.expected.update(note.card_ids())
            col.decks.select(self.parent)
            mw.moveToState("deckBrowser")
            self.later(self.parent_search, 1000)
        except Exception:
            traceback.print_exc()
            self.finish(False)

    def parent_search(self):
        host = aqt.mw.deckBrowser.modern_ui
        data = host._cards(aqt.mw.col, "", str(self.parent), "all")
        self.check(
            "parent filter includes exact parent, child and grandchild IDs",
            {int(card["id"]) for card in data["cards"]} == self.expected,
        )
        data = host._cards(aqt.mw.col, "", str(self.parent), "new")
        self.check(
            "parent filter composes with card state",
            data["total"] == len(self.expected),
        )
        self.preferences = Preferences(aqt.mw)
        self.later(self.edit_number, 1000)

    def field_id(self, native):
        return next(
            key
            for key, widget in self.preferences.modern_preferences.controls.items()
            if widget is native
        )

    def edit_number(self):
        prefs = self.preferences
        prefs.modern_preferences.schema()
        self.number_id = self.field_id(prefs.form.lrnCutoff)
        self.text_id = self.field_id(prefs.form.default_search_text)
        self.network_id = self.field_id(prefs.form.network_timeout)
        self.number = min(
            prefs.form.lrnCutoff.maximum(), prefs.form.lrnCutoff.value() + 7
        )
        prefs.modern_preferences.web.eval(
            "document.querySelectorAll('.preferences-nav nav button')[1].click()"
        )
        self.later(
            lambda: self.fill(self.number_id, str(self.number), self.number_updated)
        )

    def fill(self, key, value, next_step):
        self.preferences.modern_preferences.web.eval(
            f"(()=>{{const input=document.getElementById({json.dumps(key)});input.value={json.dumps(value)};input.dispatchEvent(new Event('input',{{bubbles:true}}));}})()"
        )
        self.later(next_step)

    def number_updated(self):
        self.check(
            "number edit reaches upstream control",
            self.preferences.form.lrnCutoff.value() == self.number,
        )
        self.preferences.modern_preferences.web.eval(
            "document.querySelectorAll('.preferences-nav nav button')[2].click()"
        )
        self.later(
            lambda: self.fill(self.text_id, "regression draft", self.text_updated)
        )

    def text_updated(self):
        self.check(
            "text edit reaches upstream control",
            self.preferences.form.default_search_text.text() == "regression draft",
        )
        self.preferences.modern_preferences.web.eval(
            "document.querySelectorAll('.preferences-nav nav button')[1].click()"
        )
        self.later(self.number_returned)

    def number_returned(self):
        self.evaluate(
            self.preferences.modern_preferences.web,
            "number survives category remount",
            f"document.getElementById({json.dumps(self.number_id)}).value === {json.dumps(str(self.number))}",
            self.return_text,
        )

    def return_text(self):
        self.preferences.modern_preferences.web.eval(
            "document.querySelectorAll('.preferences-nav nav button')[2].click()"
        )
        self.later(self.text_returned)

    def text_returned(self):
        self.evaluate(
            self.preferences.modern_preferences.web,
            "text survives category remount",
            f"document.getElementById({json.dumps(self.text_id)}).value === 'regression draft'",
            self.network_typing,
        )

    def network_typing(self):
        self.preferences.modern_preferences.web.eval(
            "document.querySelectorAll('.preferences-nav nav button')[3].click()"
        )
        self.later(self.first_digit)

    def first_digit(self):
        web = self.preferences.modern_preferences.web
        web.eval(f"document.getElementById({json.dumps(self.network_id)}).focus()")
        self.fill(self.network_id, "6", self.first_digit_visible)

    def first_digit_visible(self):
        self.evaluate(
            self.preferences.modern_preferences.web,
            "numeric intermediate digit is not replaced by the native minimum",
            f"document.getElementById({json.dumps(self.network_id)}).value === '6'",
            self.second_digit,
        )

    def second_digit(self):
        web = self.preferences.modern_preferences.web
        web.eval(
            f"(()=>{{const input=document.getElementById({json.dumps(self.network_id)});input.value += '0';input.dispatchEvent(new Event('input',{{bubbles:true}}));}})()"
        )
        self.later(self.number_complete)

    def number_complete(self):
        self.check(
            "multi-digit input reaches the intended native value",
            self.preferences.form.network_timeout.value() == 60,
        )
        self.evaluate(
            self.preferences.modern_preferences.web,
            "typing 60 leaves 60 displayed",
            f"document.getElementById({json.dumps(self.network_id)}).value === '60'",
            self.blur_clamp,
        )

    def blur_clamp(self):
        self.fill(self.network_id, "6", self.leave_number)

    def leave_number(self):
        # Background Qt webviews update activeElement without emitting focus
        # events on macOS. Dispatch the same DOM blur event used by the form.
        self.preferences.modern_preferences.web.eval(
            f"(()=>{{const input=document.getElementById({json.dumps(self.network_id)});input.blur();input.dispatchEvent(new FocusEvent('blur'));}})()"
        )
        self.later(self.number_normalized)

    def number_normalized(self):
        self.evaluate(
            self.preferences.modern_preferences.web,
            "out-of-range number normalizes on blur",
            f"document.getElementById({json.dumps(self.network_id)}).value === String({self.preferences.form.network_timeout.minimum()})",
            self.save_settings,
        )

    def save_settings(self):
        self.preferences.accept_with_callback(self.settings_saved)

    def settings_saved(self):
        self.check(
            "displayed number equals persisted preference",
            aqt.mw.col.get_preferences().scheduling.learn_ahead_secs
            == self.number * 60,
        )
        self.check(
            "displayed text equals persisted preference",
            aqt.mw.col.get_preferences().editing.default_search_text
            == "regression draft",
        )
        self.later(self.open_overview)

    def open_overview(self):
        aqt.mw.onOverview()
        self.later(self.study, 700)

    def study(self):
        aqt.mw.web.eval(
            "document.querySelector('.overview-focus-panel button').click()"
        )
        self.later(self.narrow, 800)

    def narrow(self):
        self.check(
            "review keeps upstream state",
            aqt.mw.state == "review" and aqt.mw.reviewer.state == "question",
        )
        aqt.mw.resize(400, 740)
        self.later(self.question_layout, 600)

    @staticmethod
    def visible_buttons_script():
        return """Array.from(document.querySelectorAll('button')).filter(b=>b.getClientRects().length).every(b=>{
          const r=b.getBoundingClientRect();return r.left>=-0.5 && r.right<=innerWidth+0.5 && r.top>=-0.5 && r.bottom<=innerHeight+0.5;
        })"""

    def question_layout(self):
        self.snapshot("review-question-400")
        self.evaluate(
            aqt.mw.toolbarWeb,
            "every header button fits the 400px native view",
            self.visible_buttons_script(),
            self.question_controls,
        )

    def question_controls(self):
        self.evaluate(
            aqt.mw.bottomWeb,
            "question actions fit the 400px native view",
            self.visible_buttons_script(),
            self.count_labels,
        )

    def count_labels(self):
        self.evaluate(
            aqt.mw.bottomWeb,
            "all three queues have names and distinct colors",
            """(()=>{
          const items=[...document.querySelectorAll('.queue-count')];
          return items.length===3 && ['未学习','学习中','待复习'].every(label=>items.some(item=>item.textContent.includes(label))) && new Set(items.map(item=>getComputedStyle(item.querySelector('strong')).color)).size===3;
        })()""",
            self.reveal,
        )

    def reveal(self):
        aqt.mw.bottomWeb.eval("document.getElementById('ansbut').click()")
        self.later(self.answer_layout, 600)

    def answer_layout(self):
        self.check(
            "answer still uses upstream reviewer", aqt.mw.reviewer.state == "answer"
        )
        self.snapshot("review-answer-400")
        self.evaluate(
            aqt.mw.bottomWeb,
            "all rating, edit and more buttons fit at 400px",
            self.visible_buttons_script(),
            self.rate,
        )

    def rate(self):
        self.before = aqt.mw.col.db.scalar("select count() from revlog")
        aqt.mw.bottomWeb.eval("document.getElementById('defease').click()")
        self.later(self.rated, 700)

    def rated(self):
        self.check(
            "real upstream rating creates one history record in the private copy",
            aqt.mw.col.db.scalar("select count() from revlog") == self.before + 1,
        )
        aqt.mw.resize(1200, 800)
        self.later(self.wide)

    def wide(self):
        # Background WebEngine views may throttle ResizeObserver delivery.
        attempts = getattr(self, "wide_attempts", 0)
        if not 60 <= aqt.mw.toolbarWeb.height() <= 72 and attempts < 10:
            self.wide_attempts = attempts + 1
            self.later(self.wide)
            return
        print("DESKTOP_HEADER_HEIGHT", aqt.mw.toolbarWeb.height(), flush=True)
        self.check(
            "header shrinks again at desktop width",
            60 <= aqt.mw.toolbarWeb.height() <= 72,
        )
        self.add_hooks()
        aqt.mw.moveToState("deckBrowser")
        self.later(self.deck_hook_content, 700)

    def add_hook(self, hook, callback):
        hook.append(callback)
        self.hooks.append((hook, callback))

    def add_hooks(self):
        def deck_will(browser, content):
            self.flags["deck_will"] += 1
            content.stats += """<div id="regression-deck-extension">Plugin content
              <button id="regression-deck-action" onclick="pycmd('regression-deck-action')">Plugin action</button></div>
              <script>window.regressionDeckScript=true;</script>"""

        def deck_did(browser):
            self.flags["deck_did"] += 1
            browser.web.eval(
                "window.regressionDidSawContent=!!document.getElementById('regression-deck-extension')"
            )

        def overview_will(overview, content):
            self.flags["overview_will"] += 1
            content.table += """<div id="regression-overview-extension">Plugin overview
              <button id="regression-content-action" onclick="pycmd('regression-content-action')">Plugin content action</button></div>
              <script>window.regressionOverviewScript=true;</script>"""

        def bottom(previous, links):
            self.flags["bottom"] += 1
            links.append(["", "regression-bottom-action", "Plugin bottom action"])

            def handler(command):
                if command == "regression-bottom-action":
                    self.flags["bottom_click"] += 1
                    return False
                return previous(command)

            return handler

        def message(previous, command, context):
            if command in ("regression-deck-action", "regression-content-action"):
                self.flags[
                    "deck_click"
                    if command == "regression-deck-action"
                    else "content_click"
                ] += 1
                return (True, None)
            return previous

        for hook, callback in (
            (gui_hooks.deck_browser_will_render_content, deck_will),
            (gui_hooks.deck_browser_did_render, deck_did),
            (gui_hooks.overview_will_render_content, overview_will),
            (gui_hooks.overview_will_render_bottom, bottom),
            (gui_hooks.webview_did_receive_js_message, message),
        ):
            self.add_hook(hook, callback)

    def deck_hook_content(self):
        self.evaluate(
            aqt.mw.web,
            "deck hook content, script and did-render ordering survive",
            "!!document.getElementById('regression-deck-extension') && window.regressionDeckScript===true && window.regressionDidSawContent===true",
            self.deck_hook_click,
        )

    def deck_hook_click(self):
        aqt.mw.web.eval("document.getElementById('regression-deck-action').click()")
        self.later(self.deck_clicked)

    def deck_clicked(self):
        self.check("deck extension action executes", self.flags["deck_click"] == 1)
        aqt.mw.onOverview()
        self.later(self.overview_hook_content, 700)

    def overview_hook_content(self):
        self.evaluate(
            aqt.mw.web,
            "overview hook HTML and script survive",
            "!!document.getElementById('regression-overview-extension') && window.regressionOverviewScript===true",
            self.overview_hook_click,
        )

    def overview_hook_click(self):
        aqt.mw.web.eval("document.getElementById('regression-content-action').click()")
        aqt.mw.bottomWeb.eval(
            "[...document.querySelectorAll('button')].find(b=>b.textContent.includes('Plugin bottom action')).click()"
        )
        self.later(self.plugin_actions)

    def plugin_actions(self):
        self.check("overview content action executes", self.flags["content_click"] == 1)
        self.check(
            "overview bottom action uses the returned handler",
            self.flags["bottom_click"] == 1,
        )
        self.check(
            "all legacy hooks actually run",
            all(
                self.flags[key] >= 1
                for key in ("deck_will", "deck_did", "overview_will", "bottom")
            ),
        )
        for hook, callback in self.hooks:
            hook.remove(callback)
        self.hooks.clear()
        aqt.mw.deckBrowser.modern_ui.active_page = "home"
        aqt.mw.moveToState("deckBrowser")
        self.later(self.modern_returns, 700)

    def modern_returns(self):
        self.evaluate(
            aqt.mw.web,
            "modern layout returns when legacy extensions are removed",
            "!!document.querySelector('.home-page') && !document.getElementById('regression-deck-extension')",
            lambda: self.finish(True),
        )

    def timeout(self):
        if not self.finished:
            print("FAIL regression timeout", flush=True)
            self.finish(False)

    def finish(self, passed):
        if self.finished:
            return
        self.finished = True
        self.passed = passed
        for hook, callback in self.hooks:
            hook.remove(callback)
        self.hooks.clear()
        (self.artifacts / "results.json").write_text(
            json.dumps(
                {"passed": passed, "checks": self.checks}, ensure_ascii=False, indent=2
            )
        )
        print("MODERN_UI_REGRESSIONS " + ("PASS" if passed else "FAIL"), flush=True)
        if passed:
            aqt.mw.close()
        elif hasattr(self, "preferences") and self.preferences.isVisible():
            self.preferences.accept_with_callback(aqt.mw.close)
        else:
            aqt.mw.close()


if __name__ == "__main__":
    sys.exit(run())
