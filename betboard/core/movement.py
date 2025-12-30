from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from betboard.models import EventOdds, MovementEvent


def detect_notable_moves(
    previous: EventOdds, current: EventOdds
) -> list[MovementEvent]:
    prev_map = _index_prices(previous)
    curr_map = _index_prices(current)
    moves: list[MovementEvent] = []

    for key, curr in curr_map.items():
        prev = prev_map.get(key)
        if not prev:
            continue
        market, book, outcome = key
        delta = curr["price"] - prev["price"]
        if _is_notable(market, prev["price"], curr["price"], prev["point"], curr["point"]):
            moves.append(
                MovementEvent(
                    league_key=current.event.league_key,
                    event_id=current.event.event_id,
                    created_at=datetime.now(timezone.utc),
                    details={
                        "market": market,
                        "book": book,
                        "outcome": outcome,
                        "previous": prev,
                        "current": curr,
                        "delta": delta,
                    },
                )
            )
    return moves


def _index_prices(event_odds: EventOdds) -> dict[tuple[str, str, str], dict[str, float]]:
    indexed: dict[tuple[str, str, str], dict[str, float]] = {}
    for market in event_odds.markets:
        for price in market.prices:
            indexed[(market.market, market.book, price.outcome)] = {
                "price": float(price.price),
                "point": float(market.point) if market.point is not None else None,
            }
    return indexed


def _is_notable(
    market: str,
    prev_price: float,
    curr_price: float,
    prev_point: float | None,
    curr_point: float | None,
) -> bool:
    if market == "h2h":
        if abs(curr_price - prev_price) >= 15:
            return True
        if (prev_price < 0 <= curr_price) or (prev_price > 0 >= curr_price):
            return True
    if market in {"spreads", "totals"}:
        if prev_point is None or curr_point is None:
            return False
        return abs(curr_point - prev_point) >= 1.0
    return False
