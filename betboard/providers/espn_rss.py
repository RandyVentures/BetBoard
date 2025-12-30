from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from betboard.models import Headline


RSS_FEEDS = {
    "americanfootball_nfl": "https://www.espn.com/espn/rss/nfl/news",
    "americanfootball_ncaaf": "https://www.espn.com/espn/rss/ncf/news",
    "ufc": "https://www.espn.com/espn/rss/mma/news",
}

FALLBACK_FEED = "https://www.espn.com/espn/rss/news"


class EspnRssProvider:
    name = "espn_rss"

    def fetch_headlines(self, league_key: str, limit: int) -> list[Headline]:
        url = RSS_FEEDS.get(league_key, FALLBACK_FEED)
        feed = feedparser.parse(url)
        headlines: list[Headline] = []
        for entry in feed.entries[:limit]:
            headlines.append(
                Headline(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    published_at=_parse_time(entry.get("published")),
                    source="ESPN",
                )
            )
        return headlines


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None
