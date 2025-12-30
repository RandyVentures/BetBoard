from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib


DEFAULT_CONFIG_PATH = Path.home() / ".betboard" / "config.toml"


@dataclass(frozen=True)
class OddsApiConfig:
    enabled: bool
    api_key_env: str
    api_key: str
    regions: str
    odds_format: str
    markets: list[str]


@dataclass(frozen=True)
class LeagueConfig:
    nfl_key: str
    cfb_key: str
    ufc_key: str


@dataclass(frozen=True)
class CachingConfig:
    events_ttl_minutes: int
    odds_ttl_minutes: int
    news_ttl_minutes: int


@dataclass(frozen=True)
class WatchlistConfig:
    odds_ttl_minutes_within_24h: int
    odds_ttl_minutes_within_3h: int


@dataclass(frozen=True)
class BooksConfig:
    allow: list[str]


@dataclass(frozen=True)
class AppConfig:
    refresh_ui_seconds: int
    oddsapi: OddsApiConfig
    leagues: LeagueConfig
    caching: CachingConfig
    watchlist: WatchlistConfig
    books: BooksConfig


def _get_table(config: dict[str, Any], name: str) -> dict[str, Any]:
    table = config.get(name)
    if not isinstance(table, dict):
        raise ValueError(f"Missing [{name}] in config")
    return table


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    data = tomllib.loads(config_path.read_text())

    app = _get_table(data, "app")
    oddsapi = _get_table(data, "oddsapi")
    leagues = _get_table(data, "leagues")
    caching = _get_table(data, "caching")
    watchlist = _get_table(data, "watchlist")
    books = _get_table(data, "books")

    return AppConfig(
        refresh_ui_seconds=int(app.get("refresh_ui_seconds", 30)),
        oddsapi=OddsApiConfig(
            enabled=bool(oddsapi.get("enabled", True)),
            api_key_env=str(oddsapi.get("api_key_env", "ODDS_API_KEY")),
            api_key=str(oddsapi.get("api_key", "")),
            regions=str(oddsapi.get("regions", "us")),
            odds_format=str(oddsapi.get("odds_format", "american")),
            markets=list(oddsapi.get("markets", ["h2h", "spreads", "totals"])),
        ),
        leagues=LeagueConfig(
            nfl_key=str(leagues.get("nfl_key", "americanfootball_nfl")),
            cfb_key=str(leagues.get("cfb_key", "americanfootball_ncaaf")),
            ufc_key=str(leagues.get("ufc_key", "")),
        ),
        caching=CachingConfig(
            events_ttl_minutes=int(caching.get("events_ttl_minutes", 720)),
            odds_ttl_minutes=int(caching.get("odds_ttl_minutes", 360)),
            news_ttl_minutes=int(caching.get("news_ttl_minutes", 120)),
        ),
        watchlist=WatchlistConfig(
            odds_ttl_minutes_within_24h=int(
                watchlist.get("odds_ttl_minutes_within_24h", 15)
            ),
            odds_ttl_minutes_within_3h=int(
                watchlist.get("odds_ttl_minutes_within_3h", 5)
            ),
        ),
        books=BooksConfig(allow=list(books.get("allow", []))),
    )


def odds_api_key(config: AppConfig) -> str | None:
    if config.oddsapi.api_key:
        return config.oddsapi.api_key
    return os.getenv(config.oddsapi.api_key_env)


def ensure_ufc_key(
    config: AppConfig, provider: Any, path: Path | None = None
) -> AppConfig:
    if config.leagues.ufc_key:
        return config
    sports = provider.list_sports()
    key = _discover_ufc_key(sports)
    if not key:
        return config
    config_path = path or DEFAULT_CONFIG_PATH
    _write_ufc_key(config_path, key)
    return AppConfig(
        refresh_ui_seconds=config.refresh_ui_seconds,
        oddsapi=config.oddsapi,
        leagues=LeagueConfig(
            nfl_key=config.leagues.nfl_key,
            cfb_key=config.leagues.cfb_key,
            ufc_key=key,
        ),
        caching=config.caching,
        watchlist=config.watchlist,
        books=config.books,
    )


def _discover_ufc_key(sports: list[dict[str, Any]]) -> str | None:
    candidates = []
    for sport in sports:
        key = str(sport.get("key", ""))
        title = str(sport.get("title", "")).lower()
        group = str(sport.get("group", "")).lower()
        active = bool(sport.get("active", False))
        if "ufc" in title or "ufc" in key:
            candidates.append((active, key))
        elif "mma" in key or "mma" in group or "mma" in title:
            candidates.append((active, key))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (not item[0], item[1]))
    return candidates[0][1]


def _write_ufc_key(path: Path, key: str) -> None:
    if not path.exists():
        return
    lines = path.read_text().splitlines()
    out: list[str] = []
    in_leagues = False
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_leagues and not replaced:
                out.append(f"ufc_key = \"{key}\"")
                replaced = True
            in_leagues = stripped == "[leagues]"
            out.append(line)
            continue
        if in_leagues and stripped.startswith("ufc_key"):
            out.append(f"ufc_key = \"{key}\"")
            replaced = True
            continue
        out.append(line)
    if in_leagues and not replaced:
        out.append(f"ufc_key = \"{key}\"")
    path.write_text("\n".join(out) + "\n")
