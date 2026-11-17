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


def legacy_deck_hooks() -> bool:
    from aqt import gui_hooks

    return bool(
        gui_hooks.deck_browser_will_render_content.count()
        or gui_hooks.deck_browser_did_render.count()
    )


def legacy_overview_hooks() -> bool:
    from aqt import gui_hooks

    return bool(
        gui_hooks.overview_will_render_content.count()
        or gui_hooks.overview_will_render_bottom.count()
        or gui_hooks.overview_did_refresh.count()
    )


class ModernUI:
    uses_modern_ui = True

    def __init__(self, browser: DeckBrowser) -> None:
        self.browser = browser
        self.mw = browser.mw
        self.web = browser.web
        self.active_page = "home"
        self.page_generation = 0
        self.card_filters: dict[str, str] = {}

    def render(self) -> None:
        self.page_generation += 1
        self.web.stdHtml(
            '<div id="app"></div>' + self.web.bundledScript("modern/modern.js"),
            css=["modern/modern.css"],
            js=[],
            default_css=False,
            context=self,
        )
        QWidget.setVisible(self.mw.toolbarWeb, False)
        QWidget.setVisible(self.mw.bottomWeb, False)

    def _reply(
        self,
        request_id: int,
        result: Any = None,
        error: str = "",
        generation: int | None = None,
    ) -> None:
        if generation is not None and generation != self.page_generation:
            return
        payload = json.dumps(
            {"id": request_id, "result": result, "error": error}, ensure_ascii=True
        )
        self.web.eval(f"window.ankiModernReceive?.({payload})")

    def handle(self, raw: str) -> None:
        generation = self.page_generation
        request_id = 0
        try:
            request = json.loads(raw)
            request_id = int(request["id"])
            action = request["action"]
            args = request.get("args", {})
            if action == "home":
                if args.get("navigate"):
                    self.active_page = "home"
                    if self.mw.state != "deckBrowser":
                        self.mw.moveToState("deckBrowser")
                        return
                self._query(request_id, self._home)
            elif action == "cards":
                self.active_page = "cards"
                query = str(args.get("query", ""))[:2000]
                deck_id = str(args.get("deckId", "all"))
                state = str(args.get("state", "all"))
                self.card_filters = {"query": query, "deckId": deck_id, "state": state}
                if self.mw.state != "deckBrowser":
                    self.mw.moveToState("deckBrowser")
                    return
                self._query(
                    request_id, lambda col: self._cards(col, query, deck_id, state)
                )
            elif action == "study":
                deck_id = args.get("deckId")
                if deck_id:
                    self.browser.set_current_deck(DeckId(int(deck_id)))
                else:
                    self.mw.onOverview()
                self._reply(request_id, True, generation=generation)
            elif action == "overview-action":
                allowed = {
                    "study",
                    "opts",
                    "studymore",
                    "customStudy",
                    "unbury",
                    "description",
                    "refresh",
                    "empty",
                    "review",
                }
                if args.get("command") not in allowed:
                    raise ValueError("未知操作")
                self.mw.overview._linkHandler(args["command"])
                self._reply(request_id, True, generation=generation)
            elif action == "edit":
                import aqt

                card_id = CardId(int(args["id"]))
                browser = aqt.dialogs.open("Browser", self.mw)
                browser.search_for(f"cid:{card_id}")
                self._reply(request_id, True, generation=generation)
            elif action == "rename":
                self.browser._rename(DeckId(int(args["deckId"])))
                self._reply(request_id, True, generation=generation)
            elif action == "options":
                self.browser._options(DeckId(int(args["deckId"])))
                self._reply(request_id, True, generation=generation)
            elif action == "theme":
                from aqt.theme import Theme

                self.mw.pm.set_theme(
                    Theme.LIGHT if theme_manager.night_mode else Theme.DARK
                )
                theme_manager.apply_style()
                self._reply(request_id, True, generation=generation)
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
                self._reply(request_id, True, generation=generation)
        except Exception as error:
            self._reply(request_id, error=str(error), generation=generation)

    def _query(self, request_id: int, operation: Any) -> None:
        generation = self.page_generation
        QueryOp(
            parent=self.mw,
            op=operation,
            success=lambda result: self._reply(
                request_id, result, generation=generation
            ),
        ).failure(
            lambda error: self._reply(
                request_id, error=str(error), generation=generation
            )
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
            "currentDeckId": str(col.decks.get_current_id()),
            "page": "overview" if self.mw.state == "overview" else self.active_page,
            "cardFilters": self.card_filters,
            "overview": self._overview(col) if self.mw.state == "overview" else None,
        }

    def _overview(self, col: Collection) -> dict[str, Any]:
        deck = col.decks.current()
        counts = col.sched.counts()
        info = col.sched.congratulations_info()
        return {
            "id": str(deck["id"]),
            "name": deck["name"],
            "new": counts[0],
            "learning": counts[1],
            "review": counts[2],
            "finished": col.sched._is_finished(),
            "filtered": bool(deck["dyn"]),
            "description": strip_html_media(self.mw.overview._desc(deck)),
            "buried": info.have_sched_buried or info.have_user_buried,
            "learnRemaining": info.learn_remaining,
            "nextLearnSeconds": info.secs_until_next_learn,
            "newLimitReached": info.new_remaining,
            "reviewLimitReached": info.review_remaining,
            "shared": bool(deck.get("sharedFrom")),
        }

    def _cards(
        self, col: Collection, query: str, deck_id: str, state: str
    ) -> dict[str, Any]:
        parts = [f"({query})"] if query.strip() else []
        if deck_id != "all":
            # Match the parent and every descendant, including cards temporarily
            # moved into filtered decks. IDs avoid deck-name wildcard semantics.
            ids = col.decks.deck_and_child_ids(DeckId(int(deck_id)))
            parts.append("did:" + ",".join(str(did) for did in ids))
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


def show_sync_login(mw: Any, callback: Any, username: str, password: str) -> None:
    """Present the upstream login callback in the same UI as the macOS shell."""
    import html

    from aqt.qt import QDialog, Qt, QVBoxLayout, qconnect
    from aqt.utils import disable_help_button, tr
    from aqt.webview import AnkiWebView

    dialog = QDialog(mw)
    dialog.setWindowTitle(tr.qt_misc_sync())
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    disable_help_button(dialog)
    dialog.resize(480, 560)
    dialog.setMinimumSize(440, 520)
    web = AnkiWebView(dialog)
    web.requiresCol = False
    credentials = ["", ""]

    def handle(command: str) -> bool:
        if not command.startswith("sync-login:"):
            return False
        try:
            result = json.loads(command[len("sync-login:") :])
            if result.get("accepted"):
                user = str(result.get("username", "")).strip()
                secret = str(result.get("password", ""))
                if not user or not secret:
                    return False
                credentials[:] = [user, secret]
                dialog.accept()
            else:
                dialog.reject()
        except (ValueError, TypeError):
            pass
        return False

    def finished(result: int) -> None:
        # No credentials enter localStorage, URLs, logs or generated markup.
        user, secret = (
            credentials if result == QDialog.DialogCode.Accepted else ("", "")
        )
        credentials[:] = ["", ""]
        web.cleanup()
        dialog.deleteLater()
        callback(user, secret)

    labels = html.escape(
        json.dumps(
            {
                "title": tr.qt_misc_sync(),
                "username": tr.sync_ankiweb_id_label(),
                "password": tr.sync_password_label(),
                "cancel": tr.actions_cancel(),
                "submit": tr.sync_log_in_button(),
            }
        ),
        quote=True,
    )
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(web)
    web.set_bridge_command(handle, ModernUI)
    # Retrying a rejected login keeps the username, but requires re-entering the password.
    web.stdHtml(
        f'<div id="app" data-mode="sync-login" data-username="{html.escape(username, quote=True)}" '
        f'data-dark="{str(theme_manager.night_mode).lower()}" data-labels="{labels}"></div>'
        + web.bundledScript("modern/modern.js"),
        css=["modern/modern.css"],
        js=[],
        default_css=False,
        context=ModernUI,
    )
    qconnect(dialog.finished, finished)
    dialog.open()


def render_component(
    web: Any, mode: str, metadata: dict[str, Any], context: Any
) -> None:
    import html

    context.uses_modern_ui = True
    metadata = {**metadata, "dark": theme_manager.night_mode}
    encoded = html.escape(json.dumps(metadata, ensure_ascii=True), quote=True)
    web.stdHtml(
        f'<div id="app" data-mode="{mode}" data-meta="{encoded}"></div>'
        + web.bundledScript("modern/modern.js"),
        css=["modern/modern.css"],
        js=[],
        default_css=False,
        context=context,
    )
