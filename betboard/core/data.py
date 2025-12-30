from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from betboard.config import AppConfig
from betboard.models import EventOdds, Headline, MovementEvent
from betboard.providers.espn_rss import EspnRssProvider
from betboard.providers.oddsapi import OddsApiProvider
from betboard.storage import db
from betboard.storage.cache import CacheStore


@dataclass
class LeagueData:
    league_key: str
    event_odds: Sequence[EventOdds]
    headlines: Sequence[Headline]
    movements: Sequence[MovementEvent]


def fetch_league_data(
    config: AppConfig,
    provider: OddsApiProvider,
    league_key: str,
    cache: CacheStore,
    force: bool = False,
) -> LeagueData:
    odds_key = f"odds:{league_key}"
    news_key = f"news:{league_key}"

    event_odds = None if force else cache.get(odds_key)
    if event_odds is None:
        event_odds = provider.get_odds(
            league_key=league_key,
            markets=config.oddsapi.markets,
            regions=config.oddsapi.regions,
            books_filter=config.books.allow or None,
        )
        cache.set(odds_key, event_odds, config.caching.odds_ttl_minutes)

    headlines = None if force else cache.get(news_key)
    if headlines is None:
        headlines = EspnRssProvider().fetch_headlines(league_key, limit=5)
        cache.set(news_key, headlines, config.caching.news_ttl_minutes)

    conn = db.connect()
    movements = db.list_movements(conn, league_key)

    return LeagueData(
        league_key=league_key,
        event_odds=event_odds,
        headlines=headlines,
        movements=movements,
    )
