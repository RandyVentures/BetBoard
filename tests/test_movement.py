from datetime import datetime, timezone

from betboard.core.movement import detect_notable_moves
from betboard.models import Event, EventOdds, MarketOdds, OddsPrice


def _event(event_id: str) -> Event:
    return Event(
        event_id=event_id,
        league_key="americanfootball_nfl",
        sport_title="NFL",
        home_team="Home",
        away_team="Away",
        start_time=datetime.now(timezone.utc),
    )


def test_detect_notable_moneyline_move() -> None:
    event = _event("1")
    prev = EventOdds(
        event=event,
        markets=(
            MarketOdds(
                market="h2h",
                book="book1",
                last_update=datetime.now(timezone.utc),
                prices=(OddsPrice(outcome="Home", price=-120),),
            ),
        ),
    )
    curr = EventOdds(
        event=event,
        markets=(
            MarketOdds(
                market="h2h",
                book="book1",
                last_update=datetime.now(timezone.utc),
                prices=(OddsPrice(outcome="Home", price=-90),),
            ),
        ),
    )

    moves = detect_notable_moves(prev, curr)
    assert moves, "Expected a notable move"


def test_detect_notable_spread_move() -> None:
    event = _event("2")
    prev = EventOdds(
        event=event,
        markets=(
            MarketOdds(
                market="spreads",
                book="book1",
                last_update=datetime.now(timezone.utc),
                point=-3.0,
                prices=(OddsPrice(outcome="Home", price=-110),),
            ),
        ),
    )
    curr = EventOdds(
        event=event,
        markets=(
            MarketOdds(
                market="spreads",
                book="book1",
                last_update=datetime.now(timezone.utc),
                point=-1.5,
                prices=(OddsPrice(outcome="Home", price=-110),),
            ),
        ),
    )

    moves = detect_notable_moves(prev, curr)
    assert moves, "Expected a notable spread move"
