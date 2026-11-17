# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Check the actual sync-complete callback and notice on a private fixture copy."""

from __future__ import annotations

from contextlib import ExitStack
from threading import Event
from unittest.mock import patch

# Import the shared runner before aqt so it assigns a private instance key.
from check_modern_ui_regressions import RegressionChecks, run

import aqt
from anki.sync import SyncOutput, SyncStatus
from anki.sync_pb2 import SyncAuth
from aqt import gui_hooks
from aqt.modern_notifications import show_collection_sync_complete
from aqt.qt import Qt, sip
from aqt.sync import sync_collection
from aqt.theme import Theme, theme_manager
from aqt.utils import tr


class NoticeChecks(RegressionChecks):
    def start(self):
        mw = aqt.mw
        if not mw.col or mw._background_op_count:
            self.later(self.start)
            return
        self.theme_hook_count = gui_hooks.theme_did_change.count()
        self.patches = ExitStack()
        self.release = Event()
        self.calls = {"backend": 0, "media": 0, "done": 0}
        mw.resize(960, 720)
        mw.pm.set_theme(Theme.LIGHT)
        theme_manager.apply_style()
        output = SyncOutput(required=SyncOutput.NO_CHANGES, host_number=1)

        def fake_sync(auth, media):
            self.calls["backend"] += 1
            assert self.release.wait(5), "test backend was not released"
            return output

        self.patches.enter_context(
            patch.object(mw.pm, "sync_auth", return_value=SyncAuth(hkey="test-only"))
        )
        self.patches.enter_context(
            patch.object(
                mw.col,
                "sync_status",
                return_value=SyncStatus(required=SyncStatus.NO_CHANGES),
            )
        )
        self.patches.enter_context(
            patch.object(mw.col, "sync_collection", side_effect=fake_sync)
        )
        self.patches.enter_context(
            patch.object(
                mw.media_syncer,
                "start_monitoring",
                side_effect=lambda: self.calls.__setitem__(
                    "media", self.calls["media"] + 1
                ),
            )
        )
        sync_collection(
            mw, lambda: self.calls.__setitem__("done", self.calls["done"] + 1)
        )
        self.later(self.before_complete)

    def before_complete(self):
        self.check(
            "no completion notice before the backend completes",
            getattr(aqt.mw, "_modern_sync_notice", None) is None,
        )
        self.release.set()
        self.later(self.completed, 800)

    def completed(self):
        self.notice = aqt.mw._modern_sync_notice
        self.check(
            "sync callback shows the exact collection-complete message",
            self.notice.isVisible()
            and self.notice.message.text() == tr.sync_collection_complete(),
        )
        self.check(
            "backend, media monitoring and completion callback retain their flow",
            self.calls == {"backend": 1, "media": 1, "done": 1},
        )
        self.check(
            "notice does not take keyboard focus",
            self.notice.focusPolicy() == Qt.FocusPolicy.NoFocus
            and not self.notice.hasFocus(),
        )
        self.check(
            "light notice uses the shared surface",
            "#ffffff" in self.notice.styleSheet(),
        )
        self.snapshot("sync-notice-light")
        aqt.mw.pm.set_theme(Theme.DARK)
        theme_manager.apply_style()
        self.later(self.dark)

    def dark(self):
        self.check(
            "visible notice follows dark theme", "#232938" in self.notice.styleSheet()
        )
        aqt.mw.resize(400, 600)
        self.later(self.narrow)

    def narrow(self):
        rect = self.notice.geometry()
        self.check(
            "notice stays inside a narrow window",
            rect.left() >= 0
            and rect.top() >= 0
            and rect.right() < aqt.mw.width()
            and rect.bottom() < aqt.mw.height(),
        )
        self.snapshot("sync-notice-dark-400")
        aqt.mw.moveToState("deckBrowser")
        self.later(self.page_reset)

    def page_reset(self):
        hit = aqt.mw.childAt(self.notice.geometry().center())
        self.check(
            "notice survives the sync page refresh and remains above the page",
            not sip.isdeleted(self.notice)
            and self.notice.isVisible()
            and hit is not None
            and (hit is self.notice or self.notice.isAncestorOf(hit)),
        )
        self.replacement = show_collection_sync_complete(aqt.mw)
        self.later(self.replaced)

    def replaced(self):
        self.check(
            "repeated notifications replace the previous notice",
            sip.isdeleted(self.notice) and self.replacement.isVisible(),
        )
        self.replacement.close_button.click()
        self.later(self.closed)

    def closed(self):
        self.check(
            "close control dismisses the notice", sip.isdeleted(self.replacement)
        )
        self.expiring = show_collection_sync_complete(aqt.mw, period=150)
        self.later(self.expired, 300)

    def expired(self):
        self.check("notice automatically expires", sip.isdeleted(self.expiring))
        self.check(
            "dismissal removes the theme callback",
            gui_hooks.theme_did_change.count() == self.theme_hook_count,
        )
        self.finish(True)

    def finish(self, passed):
        if hasattr(self, "release"):
            self.release.set()
        if hasattr(self, "patches"):
            self.patches.close()
        super().finish(passed)


if __name__ == "__main__":
    raise SystemExit(run(NoticeChecks))
