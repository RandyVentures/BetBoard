from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class Event:
    event_id: str
    league_key: str
    sport_title: str
    home_team: str
    away_team: str
    start_time: datetime


@dataclass(frozen=True)
class OddsPrice:
    outcome: str
    price: int


@dataclass(frozen=True)
class MarketOdds:
    market: str
    book: str
    last_update: datetime
    prices: tuple[OddsPrice, ...]
    point: float | None = None


@dataclass(frozen=True)
class EventOdds:
    event: Event
    markets: tuple[MarketOdds, ...]

    def markets_by_type(self, market: str) -> tuple[MarketOdds, ...]:
        return tuple(m for m in self.markets if m.market == market)


@dataclass(frozen=True)
class Headline:
    title: str
    url: str
    published_at: datetime | None
    source: str


@dataclass
class OddsSnapshot:
    provider: str
    league_key: str
    market: str
    fetched_at: datetime
    payload: Mapping[str, Any]


@dataclass
class WatchlistItem:
    event_id: str
    league_key: str
    added_at: datetime
    notes: str | None = None


@dataclass
class MovementEvent:
    league_key: str
    event_id: str
    created_at: datetime
    details: Mapping[str, Any]


@dataclass
class BestLines:
    market: str
    outcome: str
    price: int
    book: str
    point: float | None = None


@dataclass
class OddsBoard:
    event: Event
    best_lines: tuple[BestLines, ...]
    last_update: datetime | None


@dataclass
class ExportBundle:
    league_key: str
    events: tuple[Event, ...] = field(default_factory=tuple)
    odds: tuple[OddsBoard, ...] = field(default_factory=tuple)
    movements: tuple[MovementEvent, ...] = field(default_factory=tuple)
    headlines: tuple[Headline, ...] = field(default_factory=tuple)
    watchlist: tuple[WatchlistItem, ...] = field(default_factory=tuple)


def best_price(prices: Iterable[OddsPrice]) -> OddsPrice | None:
    best: OddsPrice | None = None
    for price in prices:
        if best is None or price.price > best.price:
            best = price
    return best
