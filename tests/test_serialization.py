from datetime import datetime, timezone

from betboard.core.serialization import event_odds_to_payload, payload_to_event_odds
from betboard.models import Event, EventOdds, MarketOdds, OddsPrice


def test_event_odds_roundtrip() -> None:
    event = Event(
        event_id="1",
        league_key="americanfootball_nfl",
        sport_title="NFL",
        home_team="Home",
        away_team="Away",
        start_time=datetime.now(timezone.utc),
    )
    odds = EventOdds(
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

    payload = event_odds_to_payload(odds)
    restored = payload_to_event_odds(payload)

    assert restored.event.event_id == odds.event.event_id
    assert restored.markets[0].book == odds.markets[0].book
    assert restored.markets[0].prices[0].price == odds.markets[0].prices[0].price
