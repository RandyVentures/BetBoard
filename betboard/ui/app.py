from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import (
    Footer,
    Header,
    ListItem,
    ListView,
    Static,
    TabbedContent,
    TabPane,
)

from betboard.config import AppConfig, ensure_ufc_key, load_config, odds_api_key
from betboard.core.data import LeagueData, fetch_league_data
from betboard.models import EventOdds
from betboard.providers.oddsapi import OddsApiProvider
from betboard.storage.cache import CacheStore
from betboard.ui.formatting import format_event, format_odds, format_side_panel


class BetBoardApp(App):
    CSS_PATH = "app.tcss"
    BINDINGS = [
        ("1", "switch_tab('NFL')", "NFL"),
        ("2", "switch_tab('CFB')", "CFB"),
        ("3", "switch_tab('UFC')", "UFC"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._config: AppConfig | None = None
        self._provider: OddsApiProvider | None = None
        self._cache: CacheStore[Any] = CacheStore()
        self._league_data: dict[str, LeagueData] = {}
        self._event_odds: dict[str, list[EventOdds]] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            yield TabPane("NFL", id="tab-nfl")
            yield TabPane("CFB", id="tab-cfb")
            yield TabPane("UFC", id="tab-ufc")
        yield Static("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._populate_tabs()
        self._load_config()
        self.call_after_refresh(self._refresh_all, False)

    def _populate_tabs(self) -> None:
        for tab_id, title in (
            ("tab-nfl", "NFL"),
            ("tab-cfb", "CFB"),
            ("tab-ufc", "UFC"),
        ):
            tab = self.query_one(f"#{tab_id}", TabPane)
            tab.mount(_build_placeholder(title, tab_id))

    def action_switch_tab(self, tab_name: str) -> None:
        tabs = self.query_one(TabbedContent)
        tabs.active = tab_name

    def action_refresh(self) -> None:
        self._refresh_all(force=True)

    def _load_config(self) -> None:
        try:
            self._config = load_config()
        except FileNotFoundError:
            self._config = None
            return
        key = odds_api_key(self._config)
        if not key:
            self._provider = None
            return
        self._provider = OddsApiProvider(key)
        self._config = ensure_ufc_key(self._config, self._provider)

    def _refresh_all(self, force: bool) -> None:
        if not self._config or not self._provider:
            self._set_status(
                "Missing config or ODDS_API_KEY. Check ~/.betboard/config.toml."
            )
            return
        for tab_id, league_key in _league_map(self._config).items():
            self._refresh_league(tab_id, league_key, force)

    def _refresh_league(self, tab_id: str, league_key: str, force: bool) -> None:
        assert self._config is not None
        assert self._provider is not None
        try:
            league_data = fetch_league_data(
                self._config, self._provider, league_key, self._cache, force=force
            )
        except Exception as exc:
            self._render_error(tab_id, f"Fetch error: {exc}")
            self._set_status(f"{league_key}: fetch error")
            return
        self._league_data[league_key] = league_data
        self._event_odds[league_key] = list(league_data.event_odds)
        self._update_tab(tab_id, league_key, league_data)
        self._set_status(
            f"{league_key}: {len(league_data.event_odds)} events, {len(league_data.headlines)} headlines"
        )

    def _update_tab(self, tab_id: str, league_key: str, league_data: LeagueData) -> None:
        list_view = self.query_one(f"#events-{tab_id}", ListView)
        list_view.clear()
        list_view.data = {"tab_id": tab_id}
        for odds in league_data.event_odds:
            list_view.append(ListItem(Static(format_event(odds.event))))
        if not league_data.event_odds:
            list_view.append(ListItem(Static("No events returned.")))
        self._update_side_panels(tab_id, league_data)

    def _update_side_panels(self, tab_id: str, league_data: LeagueData) -> None:
        odds_panel = self.query_one(f"#odds-{tab_id}", Static)
        news_panel = self.query_one(f"#news-{tab_id}", Static)
        if league_data.event_odds:
            odds_panel.update(format_odds(league_data.event_odds[0]))
        else:
            odds_panel.update("No odds available")
        news_panel.update(
            format_side_panel(league_data.headlines, league_data.movements)
        )

    def _set_status(self, message: str) -> None:
        status = self.query_one("#status", Static)
        status.update(message)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        list_view = event.list_view
        tab_id = list_view.data.get("tab_id") if list_view.data else None
        if not tab_id or not self._config:
            return
        league_key = _league_map(self._config).get(tab_id)
        if not league_key:
            return
        items = self._event_odds.get(league_key, [])
        if not items:
            return
        idx = list_view.index
        if idx is None or idx >= len(items):
            return
        odds_panel = self.query_one(f"#odds-{tab_id}", Static)
        odds_panel.update(format_odds(items[idx]))

    def _render_error(self, tab_id: str, message: str) -> None:
        list_view = self.query_one(f"#events-{tab_id}", ListView)
        list_view.clear()
        list_view.append(ListItem(Static(message)))
        odds_panel = self.query_one(f"#odds-{tab_id}", Static)
        news_panel = self.query_one(f"#news-{tab_id}", Static)
        odds_panel.update(message)
        news_panel.update(message)


def _build_placeholder(title: str, tab_id: str) -> Horizontal:
    events = ListView(
        ListItem(Static(f"{title} events will appear here")),
        classes="pane events",
        id=f"events-{tab_id}",
    )
    events.data = {"tab_id": tab_id}
    odds = Static("Odds board", classes="pane", id=f"odds-{tab_id}")
    news = Static(
        "Movements + news", classes="pane", id=f"news-{tab_id}"
    )
    return Horizontal(events, odds, news, classes="pane-row")


def _league_map(config: AppConfig) -> dict[str, str]:
    return {
        "tab-nfl": config.leagues.nfl_key,
        "tab-cfb": config.leagues.cfb_key,
        "tab-ufc": config.leagues.ufc_key or "ufc",
    }
