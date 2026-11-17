# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Exercise native home selection and live sync-state bridge in a private copy."""

from check_modern_ui_regressions import RegressionChecks, run

import aqt
from aqt.theme import Theme, theme_manager


class HomeActions(RegressionChecks):
    def start(self):
        if not aqt.mw.col or aqt.mw._background_op_count:
            self.later(self.start)
            return
        aqt.mw.resize(400, 740)
        aqt.mw.pm.set_theme(Theme.DARK)
        theme_manager.apply_style()
        aqt.mw.moveToState("deckBrowser")
        self.later(self.select, 800)

    def select(self):
        aqt.mw.web.eval(
            "(()=>{const s=document.querySelector('.split-mobile-picker select');s.value=s.options[1].value;s.dispatchEvent(new Event('change',{bubbles:true}));})()"
        )
        self.later(self.selected)

    def selected(self):
        col = aqt.mw.col
        data = aqt.mw.deckBrowser.modern_ui._home(col)
        self.check(
            "deck totals include every descendant",
            all(
                deck["total"]
                == col.db.scalar(
                    "select count() from cards where did in ("
                    + ",".join(
                        str(i) for i in col.decks.deck_and_child_ids(int(deck["id"]))
                    )
                    + ")"
                )
                for deck in data["decks"]
            ),
        )
        self.evaluate(
            aqt.mw.web,
            "selecting a row keeps the home and selects that row",
            "document.querySelector('.split-focus h1').textContent===document.querySelector('.split-mobile-picker select').selectedOptions[0].textContent && !!document.querySelector('.home-page')",
            self.sync,
        )

    def sync(self):
        mw = aqt.mw
        mw._modern_collection_complete = mw.pm.name + " other profile"
        mw.web.eval(
            "(()=>{const original=window.ankiModernReceive;window.ankiModernReceive=m=>{if(m.id===98765){window.syncProfileCheck=m.result.collectionComplete===false;window.ankiModernReceive=original;}else{original(m);}};window.pycmd('modern:'+JSON.stringify({id:98765,action:'sync-status'}));})()"
        )
        self.later(self.sync_result, 300)

    def sync_result(self):
        self.evaluate(
            aqt.mw.web,
            "completion state never leaks across profiles",
            "window.syncProfileCheck===true",
            self.live,
        )

    def live(self):
        mw = aqt.mw
        self.original = (mw.media_syncer._syncing, mw.media_syncer.last_progress)
        mw._modern_collection_complete = mw.pm.name
        mw.media_syncer._syncing = True
        mw.media_syncer.last_progress = "正在检查测试媒体"
        mw.web.eval("document.querySelector('.sync-status-trigger').click()")
        self.later(self.panel, 600)

    def panel(self):
        self.snapshot("sync-state-400")
        self.evaluate(
            aqt.mw.web,
            "live media status is shown without declaring all sync complete",
            "(()=>{const p=document.querySelector('.sync-status-panel');const r=p.getBoundingClientRect();return p.textContent.includes('正在检查测试媒体')&&p.textContent.includes('媒体仍在同步')&&r.left>=0&&r.right<=innerWidth;})()",
            self.study,
        )

    def study(self):
        mw = aqt.mw
        mw.media_syncer._syncing, mw.media_syncer.last_progress = self.original
        mw.web.eval("document.querySelector('.split-study-action').click()")
        self.later(self.overview, 800)

    def overview(self):
        self.check(
            "start action enters the actual upstream reviewer", aqt.mw.state == "review"
        )
        self.finish(True)


if __name__ == "__main__":
    raise SystemExit(run(HomeActions))
