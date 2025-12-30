from __future__ import annotations

from datetime import datetime
from typing import Iterable

from betboard.models import BestLines, EventOdds, OddsBoard, OddsPrice


def build_odds_board(event_odds: EventOdds) -> OddsBoard:
    best_lines: list[BestLines] = []
    last_updates: list[datetime] = []

    for market in event_odds.markets:
        last_updates.append(market.last_update)
        for price in market.prices:
            existing = _find_line(best_lines, market.market, price.outcome)
            if existing is None or _is_better(price, market.point, existing):
                if existing:
                    best_lines.remove(existing)
                best_lines.append(
                    BestLines(
                        market=market.market,
                        outcome=price.outcome,
                        price=price.price,
                        book=market.book,
                        point=market.point,
                    )
                )

    return OddsBoard(
        event=event_odds.event,
        best_lines=tuple(best_lines),
        last_update=max(last_updates) if last_updates else None,
    )


def _find_line(
    lines: Iterable[BestLines], market: str, outcome: str
) -> BestLines | None:
    for line in lines:
        if line.market == market and line.outcome == outcome:
            return line
    return None


def _is_better(price: OddsPrice, point: float | None, existing: BestLines) -> bool:
    if price.price != existing.price:
        return price.price > existing.price
    if point is None or existing.point is None:
        return False
    return point > existing.point
