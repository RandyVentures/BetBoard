from __future__ import annotations

from datetime import datetime
from typing import Iterable

from betboard.core.normalization import build_odds_board
from betboard.models import Event, EventOdds, Headline, MovementEvent, OddsBoard


def format_event(event: Event) -> str:
    local = event.start_time.astimezone()
    when = local.strftime("%b %d %H:%M")
    return f"{event.away_team} @ {event.home_team}  {when}"


def format_odds(event_odds: EventOdds) -> str:
    board = build_odds_board(event_odds)
    return format_odds_board(board)


def format_odds_board(board: OddsBoard) -> str:
    if not board.best_lines:
        return "No odds available"
    lines = [
        "market | outcome | price | point | book",
        "-" * 48,
    ]
    for line in board.best_lines:
        point = "" if line.point is None else f"{line.point:+.1f}"
        lines.append(
            f"{line.market:7} | {line.outcome:8} | {line.price:>5} | {point:>5} | {line.book}"
        )
    if board.last_update:
        lines.append("")
        lines.append(f"Updated: {board.last_update.astimezone().strftime('%b %d %H:%M')}")
    return "\n".join(lines)


def format_headlines(headlines: Iterable[Headline]) -> str:
    lines = ["Headlines", "-" * 24]
    for headline in headlines:
        lines.append(f"- {headline.title}")
    return "\n".join(lines)


def format_movements(movements: Iterable[MovementEvent]) -> str:
    lines = ["Notable Moves", "-" * 24]
    for movement in list(movements)[:5]:
        details = movement.details
        market = details.get("market", "")
        outcome = details.get("outcome", "")
        delta = details.get("delta", "")
        book = details.get("book", "")
        lines.append(f"- {market} {outcome} {delta:+} ({book})")
    return "\n".join(lines)


def format_side_panel(headlines: Iterable[Headline], movements: Iterable[MovementEvent]) -> str:
    return f"{format_movements(movements)}\n\n{format_headlines(headlines)}"
