# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""macOS presentation layer. Collection changes stay in upstream operations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from anki.cards import CardId
from anki.decks import DeckId
from anki.utils import strip_html_media
from aqt.operations import QueryOp
from aqt.qt import QWidget
from aqt.theme import theme_manager
from aqt.utils import aqt_data_path

if TYPE_CHECKING:
    from anki.collection import Collection
    from aqt.deckbrowser import DeckBrowser


def available() -> bool:
    return (aqt_data_path() / "web/modern/modern.js").is_file()


class ModernUI:
    uses_modern_ui = True

    def __init__(self, browser: DeckBrowser) -> None:
        self.browser = browser
        self.mw = browser.mw
        self.web = browser.web
        self.active_page = "home"

    def render(self) -> None:
        self.web.stdHtml(
            '<div id="app"></div>' + self.web.bundledScript("modern/modern.js"),
            css=["modern/modern.css"],
            js=[],
            default_css=False,
            context=self,
        )
        QWidget.setVisible(self.mw.toolbarWeb, False)
        QWidget.setVisible(self.mw.bottomWeb, False)

    def _reply(self, request_id: int, result: Any = None, error: str = "") -> None:
        payload = json.dumps(
            {"id": request_id, "result": result, "error": error}, ensure_ascii=True
        )
        self.web.eval(f"window.ankiModernReceive?.({payload})")

    def handle(self, raw: str) -> None:
        request_id = 0
        try:
            request = json.loads(raw)
            request_id = int(request["id"])
            action = request["action"]
            args = request.get("args", {})
            if action == "home":
                if args.get("navigate"):
                    self.active_page = "home"
                self._query(request_id, self._home)
            elif action == "cards":
                self.active_page = "cards"
                query = str(args.get("query", ""))[:2000]
                deck_id = str(args.get("deckId", "all"))
                state = str(args.get("state", "all"))
                self._query(
                    request_id, lambda col: self._cards(col, query, deck_id, state)
                )
            elif action == "study":
                deck_id = args.get("deckId")
                if deck_id:
                    self.browser.set_current_deck(DeckId(int(deck_id)))
                else:
                    self.mw.onOverview()
                self._reply(request_id, True)
            elif action == "edit":
                import aqt

                card_id = CardId(int(args["id"]))
                browser = aqt.dialogs.open("Browser", self.mw)
                browser.search_for(f"cid:{card_id}")
                self._reply(request_id, True)
            elif action == "rename":
                self.browser._rename(DeckId(int(args["deckId"])))
                self._reply(request_id, True)
            elif action == "options":
                self.browser._options(DeckId(int(args["deckId"])))
                self._reply(request_id, True)
            elif action == "theme":
                from aqt.theme import Theme

                self.mw.pm.set_theme(
                    Theme.LIGHT if theme_manager.night_mode else Theme.DARK
                )
                theme_manager.apply_style()
                self._reply(request_id, True)
            else:
                actions = {
                    "add": self.mw.onAddCard,
                    "browse": self.mw.onBrowse,
                    "stats": self.mw.onStats,
                    "settings": self.mw.onPrefs,
                    "sync": self.mw.on_sync_button_clicked,
                    "create": self.browser._on_create,
                    "import": self.mw.onImport,
                }
                if action not in actions:
                    raise ValueError("未知操作")
                actions[action]()
                self._reply(request_id, True)
        except Exception as error:
            self._reply(request_id, error=str(error))

    def _query(self, request_id: int, operation: Any) -> None:
        QueryOp(
            parent=self.mw,
            op=operation,
            success=lambda result: self._reply(request_id, result),
        ).failure(
            lambda error: self._reply(request_id, error=str(error))
        ).run_in_background()

    def _home(self, col: Collection) -> dict[str, Any]:
        tree = col.sched.deck_due_tree()
        decks = []

        def walk(node: Any, ancestors: str = "") -> None:
            for child in node.children:
                name = f"{ancestors}::{child.name}" if ancestors else child.name
                decks.append(
                    {
                        "id": str(child.deck_id),
                        "name": name,
                        "description": "按牌组的学习限制安排",
                        "color": "blue",
                        "icon": "book",
                        "new": child.new_count,
                        "learning": child.learn_count,
                        "review": child.review_count,
                        "level": child.level,
                    }
                )
                walk(child, name)

        walk(tree)
        cutoff = col.sched.day_cutoff
        activity = []
        for i in range(27, -1, -1):
            end = (cutoff - i * 86400) * 1000
            activity.append(
                col.db.scalar(
                    "select count() from revlog where id >= ? and id < ? and type < 4",
                    end - 86400000,
                    end,
                )
                or 0
            )
        return {
            "decks": decks,
            "new": tree.new_count,
            "learning": tree.learn_count,
            "review": tree.review_count,
            "studiedToday": col.studied_today(),
            "completed": activity[-1],
            "activity": activity,
            "total": col.card_count(),
            "dark": theme_manager.night_mode,
            "profile": self.mw.pm.name,
            "page": self.active_page,
        }

    def _cards(
        self, col: Collection, query: str, deck_id: str, state: str
    ) -> dict[str, Any]:
        parts = [f"({query})"] if query.strip() else []
        if deck_id != "all":
            # Numeric deck IDs cannot introduce search operators.
            parts.append(f"did:{int(deck_id)}")
        filters = {
            "new": "is:new",
            "learning": "is:learn",
            "review": "is:review is:due",
        }
        if state in filters:
            parts.append(filters[state])
        ids = col.find_cards(" ".join(parts), order=True)
        cards = []
        for card_id in ids[:100]:
            card = col.get_card(card_id)
            note = card.note()
            cards.append(
                {
                    "id": str(card.id),
                    "deckId": str(card.did),
                    "front": strip_html_media(note.fields[0])[:2000]
                    if note.fields
                    else "",
                    "back": strip_html_media(note.fields[1])[:4000]
                    if len(note.fields) > 1
                    else "",
                    "fields": [
                        {"name": name, "text": strip_html_media(value)[:6000]}
                        for name, value in note.items()
                    ],
                    "tags": note.tags,
                    "type": note.note_type()["name"],
                    "state": "new"
                    if card.type == 0
                    else "learning"
                    if card.type in (1, 3)
                    else "review",
                    "suspended": card.queue == -1,
                }
            )
        return {"cards": cards, "total": len(ids)}
