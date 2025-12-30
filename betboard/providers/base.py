from __future__ import annotations

from typing import Protocol

from betboard.models import Event, EventOdds, Headline


class OddsProvider(Protocol):
    name: str

    def list_events(self, league_key: str, hours: int) -> list[Event]:
        raise NotImplementedError

    def get_odds(
        self,
        league_key: str,
        markets: list[str],
        regions: str,
        books_filter: list[str] | None,
    ) -> list[EventOdds]:
        raise NotImplementedError


class NewsProvider(Protocol):
    name: str

    def fetch_headlines(self, league_key: str, limit: int) -> list[Headline]:
        raise NotImplementedError
