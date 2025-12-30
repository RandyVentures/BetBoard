from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from betboard.models import Event, EventOdds, MarketOdds, OddsPrice


class OddsApiProvider:
    name = "oddsapi"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("Missing Odds API key")
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"

    def list_events(self, league_key: str, hours: int) -> list[Event]:
        url = f"{self.base_url}/sports/{league_key}/events"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        cutoff = datetime.now(tz=timezone.utc)
        events: list[Event] = []
        for raw in data:
            start_time = _parse_time(raw.get("commence_time"))
            if start_time and (start_time - cutoff).total_seconds() > hours * 3600:
                continue
            events.append(
                Event(
                    event_id=raw.get("id"),
                    league_key=league_key,
                    sport_title=raw.get("sport_title", ""),
                    home_team=raw.get("home_team", ""),
                    away_team=raw.get("away_team", ""),
                    start_time=start_time or cutoff,
                )
            )
        return events

    def get_odds(
        self,
        league_key: str,
        markets: list[str],
        regions: str,
        books_filter: list[str] | None,
    ) -> list[EventOdds]:
        url = f"{self.base_url}/sports/{league_key}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": ",".join(markets),
            "oddsFormat": "american",
        }
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        return [_parse_event_odds(league_key, raw, books_filter) for raw in data]

    def list_sports(self) -> list[dict[str, Any]]:
        url = f"{self.base_url}/sports"
        params = {"apiKey": self.api_key}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()


def _parse_event_odds(
    league_key: str,
    raw: dict[str, Any],
    books_filter: list[str] | None,
) -> EventOdds:
    event = Event(
        event_id=raw.get("id"),
        league_key=league_key,
        sport_title=raw.get("sport_title", ""),
        home_team=raw.get("home_team", ""),
        away_team=raw.get("away_team", ""),
        start_time=_parse_time(raw.get("commence_time")) or datetime.now(timezone.utc),
    )
    markets: list[MarketOdds] = []
    for bookmaker in raw.get("bookmakers", []):
        if books_filter and bookmaker.get("key") not in books_filter:
            continue
        book_key = bookmaker.get("key") or "unknown"
        for market in bookmaker.get("markets", []):
            market_key = market.get("key")
            last_update = _parse_time(market.get("last_update")) or datetime.now(
                timezone.utc
            )
            point = None
            prices: list[OddsPrice] = []
            for outcome in market.get("outcomes", []):
                price = outcome.get("price")
                if price is None:
                    continue
                if outcome.get("point") is not None:
                    point = float(outcome.get("point"))
                prices.append(OddsPrice(outcome=str(outcome.get("name")), price=int(price)))
            markets.append(
                MarketOdds(
                    market=market_key,
                    book=book_key,
                    last_update=last_update,
                    prices=tuple(prices),
                    point=point,
                )
            )
    return EventOdds(event=event, markets=tuple(markets))


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
