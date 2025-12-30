from __future__ import annotations

from datetime import datetime
from typing import Any

from betboard.models import Event, EventOdds, MarketOdds, OddsPrice


def event_odds_to_payload(event_odds: EventOdds) -> dict[str, Any]:
    return {
        "event": {
            "event_id": event_odds.event.event_id,
            "league_key": event_odds.event.league_key,
            "sport_title": event_odds.event.sport_title,
            "home_team": event_odds.event.home_team,
            "away_team": event_odds.event.away_team,
            "start_time": event_odds.event.start_time.isoformat(),
        },
        "markets": [
            {
                "market": market.market,
                "book": market.book,
                "last_update": market.last_update.isoformat(),
                "point": market.point,
                "prices": [
                    {"outcome": price.outcome, "price": price.price}
                    for price in market.prices
                ],
            }
            for market in event_odds.markets
        ],
    }


def payload_to_event_odds(payload: dict[str, Any]) -> EventOdds:
    event_raw = payload["event"]
    event = Event(
        event_id=event_raw["event_id"],
        league_key=event_raw["league_key"],
        sport_title=event_raw.get("sport_title", ""),
        home_team=event_raw.get("home_team", ""),
        away_team=event_raw.get("away_team", ""),
        start_time=datetime.fromisoformat(event_raw["start_time"]),
    )
    markets: list[MarketOdds] = []
    for market_raw in payload.get("markets", []):
        markets.append(
            MarketOdds(
                market=market_raw["market"],
                book=market_raw["book"],
                last_update=datetime.fromisoformat(market_raw["last_update"]),
                prices=tuple(
                    OddsPrice(outcome=price["outcome"], price=int(price["price"]))
                    for price in market_raw.get("prices", [])
                ),
                point=market_raw.get("point"),
            )
        )
    return EventOdds(event=event, markets=tuple(markets))
