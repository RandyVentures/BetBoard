from __future__ import annotations

from betboard.models import Event, EventOdds


class TheRundownProvider:
    name = "therundown"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("Missing TheRundown API key")
        self.api_key = api_key

    def list_events(self, league_key: str, hours: int) -> list[Event]:
        raise NotImplementedError("TheRundown provider is not wired in yet")

    def get_odds(
        self,
        league_key: str,
        markets: list[str],
        regions: str,
        books_filter: list[str] | None,
    ) -> list[EventOdds]:
        raise NotImplementedError("TheRundown provider is not wired in yet")
