# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Check compact preferences, real algorithm navigation, and sync sheets."""

from check_modern_ui_regressions import RegressionChecks, run

import aqt
from aqt import gui_hooks
from aqt.deckoptions import DeckOptionsDialog
from aqt.mediasync import MediaSyncDialog
from aqt.preferences import Preferences
from aqt.progress import ProgressDialog
from aqt.qt import QApplication, QDialog, QPushButton
from aqt.sync import get_id_and_pass_from_user
from aqt.theme import Theme, theme_manager
from aqt.webview import AnkiWebView


class LayoutChecks(RegressionChecks):
    def start(self):
        if not aqt.mw.col or aqt.mw._background_op_count:
            self.later(self.start)
            return
        self.fsrs = aqt.mw.col.get_config("fsrs", False)
        aqt.mw.pm.set_theme(Theme.LIGHT)
        theme_manager.apply_style()
        self.preferences = Preferences(aqt.mw)
        self.later(self.preferences_ready, 800)

    def preferences_ready(self):
        prefs = self.preferences
        self.check(
            "preferences opens at compact size",
            prefs.width() <= 800 and prefs.height() <= 600,
        )
        prefs.grab().save(str(self.artifacts / "preferences-light.png"))
        prefs.modern_preferences.web.eval(
            "document.querySelectorAll('.preferences-nav nav button')[7].click()"
        )
        self.later(self.algorithm)

    def algorithm(self):
        self.preferences.grab().save(str(self.artifacts / "algorithm-light.png"))
        self.evaluate(
            self.preferences.modern_preferences.web,
            "algorithm status and real settings location are visible",
            "(()=>{const c=document.querySelector('.algorithm-card');const b=c?.querySelector('button');return !!b&&c.textContent.includes('FSRS')&&b.getBoundingClientRect().bottom<innerHeight;})()",
            self.open_options,
        )

    def open_options(self):
        self.preferences.modern_preferences.web.eval(
            "document.querySelector('.algorithm-card button').click()"
        )
        self.later(self.options, 1400)

    def options(self):
        options = [
            w
            for w in QApplication.topLevelWidgets()
            if isinstance(w, DeckOptionsDialog) and w.isVisible()
        ]
        self.check(
            "algorithm button opens upstream deck options after saving preferences",
            len(options) == 1 and not self.preferences.isVisible(),
        )
        self.check(
            "viewing algorithm does not change FSRS",
            self.fsrs == aqt.mw.col.get_config("fsrs", False),
        )
        options[0].require_close()
        self.dark = False
        self.login()

    def login(self):
        aqt.mw.pm.set_theme(Theme.DARK if self.dark else Theme.LIGHT)
        theme_manager.apply_style()
        get_id_and_pass_from_user(
            aqt.mw,
            lambda u, p: self.check("cancel returns no credentials", u == p == ""),
        )
        self.later(self.login_ready, 800)

    def login_ready(self):
        self.dialog = next(
            w
            for w in QApplication.topLevelWidgets()
            if isinstance(w, QDialog)
            and w.isVisible()
            and w.findChildren(AnkiWebView)
            and w is not aqt.mw
        )
        self.dialog.grab().save(
            str(self.artifacts / ("login-dark.png" if self.dark else "login-light.png"))
        )
        web = self.dialog.findChild(AnkiWebView)
        self.evaluate(
            web,
            "login fields and submit fit the compact window",
            "(()=>{const b=document.querySelector('button[type=submit]');return !!document.querySelector('#sync-password[type=password]')&&b.disabled&&b.getBoundingClientRect().bottom<=innerHeight&&document.documentElement.scrollHeight<=innerHeight;})()",
            self.progress,
        )

    def progress(self):
        self.dialog.reject()
        self.progress_dialog = ProgressDialog(aqt.mw)
        self.progress_dialog.setWindowTitle("同步")
        self.progress_dialog.form.label.setText(
            "正在同步学习记录…\n已接收 128 KB · 已发送 64 KB"
        )
        self.progress_dialog.form.progressBar.setRange(0, 100)
        self.progress_dialog.form.progressBar.setValue(45)
        self.progress_dialog.show()
        self.later(self.progress_ready, 350)

    def progress_ready(self):
        p = self.progress_dialog
        p.grab().save(
            str(
                self.artifacts
                / ("progress-dark.png" if self.dark else "progress-light.png")
            )
        )
        button = p.findChild(QPushButton)
        self.check(
            "progress status and cancellation fit the sheet",
            p.width() <= 460
            and p.height() <= 300
            and p.rect().contains(button.geometry())
            and p.form.label.isVisible(),
        )
        button.click()
        self.check("cancel still signals the original progress flow", p.wantCancel)
        p.cancel()
        if self.dark:
            self.media()
        else:
            self.dark = True
            self.login()

    def media(self):
        class FakeSyncer:
            last_progress = "已添加 12 个文件 · 已检查 128 个文件"
            aborted = False

            def is_syncing(self):
                return not self.aborted

            def abort(self):
                self.aborted = True

        self.syncer = FakeSyncer()
        self.media_dialog = MediaSyncDialog(aqt.mw, self.syncer)
        self.later(self.media_ready)

    def media_ready(self):
        p = self.media_dialog
        p.grab().save(str(self.artifacts / "media-dark.png"))
        self.check(
            "media status is readable without a timestamp prefix",
            p.form.log_label.text() == self.syncer.last_progress,
        )
        p.abort_button.click()
        self.check(
            "media abort still reaches upstream syncer",
            self.syncer.aborted and p.abort_button.isHidden(),
        )
        gui_hooks.media_sync_did_progress.remove(p._on_log_entry)
        gui_hooks.media_sync_did_start_or_stop.remove(p._on_start_stop)
        p.close()
        self.finish(True)


if __name__ == "__main__":
    raise SystemExit(run(LayoutChecks))
