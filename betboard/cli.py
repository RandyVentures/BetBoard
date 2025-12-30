from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from betboard.config import AppConfig, ensure_ufc_key, load_config, odds_api_key
from betboard.core.movement import detect_notable_moves
from betboard.core.normalization import build_odds_board
from betboard.core.serialization import event_odds_to_payload, payload_to_event_odds
from betboard.models import ExportBundle, MovementEvent, OddsSnapshot, WatchlistItem
from betboard.providers.espn_rss import EspnRssProvider
from betboard.providers.oddsapi import OddsApiProvider
from betboard.storage import db
from betboard.ui.app import BetBoardApp


def main() -> None:
    parser = argparse.ArgumentParser(prog="betboard")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run")

    refresh = sub.add_parser("refresh")
    refresh.add_argument("--league", choices=["NFL", "CFB", "UFC"], default=None)
    refresh.add_argument("--force", action="store_true")

    export = sub.add_parser("export")
    export.add_argument("--league", choices=["NFL", "CFB", "UFC"])
    export.add_argument("--all", action="store_true")
    export.add_argument("--format", default="json", choices=["json"])
    export.add_argument("--output-dir", default=None)

    watchlist = sub.add_parser("watchlist")
    watchlist_sub = watchlist.add_subparsers(dest="watchlist_command")
    watchlist_add = watchlist_sub.add_parser("add")
    watchlist_add.add_argument("event_id")
    watchlist_add.add_argument("--league", required=True, choices=["NFL", "CFB", "UFC"])
    watchlist_sub.add_parser("list")
    watchlist_remove = watchlist_sub.add_parser("remove")
    watchlist_remove.add_argument("event_id")

    args = parser.parse_args()

    if args.command == "run":
        BetBoardApp().run()
        return

    if args.command == "refresh":
        _refresh(args.league, args.force)
        return

    if args.command == "export":
        _export(args)
        return

    if args.command == "watchlist":
        _handle_watchlist(args)
        return

    parser.print_help()


def _refresh(league: str | None, force: bool) -> None:
    config = load_config()
    conn = db.connect()
    provider = _odds_provider(config)
    if provider is None:
        raise SystemExit("Odds provider not enabled or missing API key")
    config = ensure_ufc_key(config, provider)
    leagues = _resolve_leagues(config, league)

    for league_key in leagues:
        event_odds = provider.get_odds(
            league_key=league_key,
            markets=config.oddsapi.markets,
            regions=config.oddsapi.regions,
            books_filter=config.books.allow or None,
        )
        for market in config.oddsapi.markets:
            payload = [
                event_odds_to_payload(odds)
                for odds in event_odds
                if any(m.market == market for m in odds.markets)
            ]
            snapshot = OddsSnapshot(
                provider=provider.name,
                league_key=league_key,
                market=market,
                fetched_at=datetime.utcnow(),
                payload={"items": payload},
            )
            prev_payload = db.get_event_snapshot_payload(
                conn, provider.name, league_key, market
            )
            db.add_snapshot(conn, snapshot)
            if prev_payload:
                _detect_and_store_movements(
                    conn, prev_payload, snapshot.payload, league_key
                )


def _detect_and_store_movements(
    conn: Any,
    prev_payload: dict[str, Any],
    curr_payload: dict[str, Any],
    league_key: str,
) -> None:
    prev_items = {
        item["event"]["event_id"]: payload_to_event_odds(item)
        for item in prev_payload.get("items", [])
    }
    movements: list[MovementEvent] = []
    for item in curr_payload.get("items", []):
        current = payload_to_event_odds(item)
        previous = prev_items.get(current.event.event_id)
        if not previous:
            continue
        movements.extend(detect_notable_moves(previous, current))
    if movements:
        db.record_movement_events(conn, movements)


def _export(args: argparse.Namespace) -> None:
    config = load_config()
    provider = _odds_provider(config)
    if provider is None:
        raise SystemExit("Odds provider not enabled or missing API key")
    config = ensure_ufc_key(config, provider)
    if not args.all and not args.league:
        raise SystemExit("Provide --league or --all")

    leagues = _resolve_leagues(config, args.league) if args.league else _resolve_leagues(config, None)
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    for league_key in leagues:
        event_odds = provider.get_odds(
            league_key=league_key,
            markets=config.oddsapi.markets,
            regions=config.oddsapi.regions,
            books_filter=config.books.allow or None,
        )
        odds_boards = tuple(build_odds_board(odds) for odds in event_odds)

        news_provider = EspnRssProvider()
        headlines = tuple(news_provider.fetch_headlines(league_key, limit=5))

        conn = db.connect()
        movements = tuple(db.list_movements(conn, league_key))
        watchlist_items = tuple(
            item for item in db.list_watchlist(conn) if item.league_key == league_key
        )

        bundle = ExportBundle(
            league_key=league_key,
            events=tuple(odds.event for odds in event_odds),
            odds=odds_boards,
            movements=movements,
            headlines=headlines,
            watchlist=watchlist_items,
        )

        payload = _to_json(bundle)
        if output_dir:
            suffix = _league_suffix(league_key)
            (output_dir / f"{suffix}.json").write_text(payload)
        else:
            print(payload)


def _handle_watchlist(args: argparse.Namespace) -> None:
    conn = db.connect()
    if args.watchlist_command == "add":
        config = load_config()
        provider = _odds_provider(config)
        if provider is None:
            raise SystemExit("Odds provider not enabled or missing API key")
        config = ensure_ufc_key(config, provider)
        league_key = _resolve_leagues(config, args.league)[0]
        item = WatchlistItem(
            event_id=args.event_id,
            league_key=league_key,
            added_at=datetime.utcnow(),
        )
        db.upsert_watchlist(conn, item)
        print(f"Added {args.event_id}")
        return

    if args.watchlist_command == "remove":
        db.remove_watchlist(conn, args.event_id)
        print(f"Removed {args.event_id}")
        return

    if args.watchlist_command == "list":
        items = db.list_watchlist(conn)
        for item in items:
            print(f"{item.event_id} ({item.league_key})")
        return

    raise SystemExit("Unknown watchlist command")


def _odds_provider(config: AppConfig) -> OddsApiProvider | None:
    if not config.oddsapi.enabled:
        return None
    key = odds_api_key(config)
    if not key:
        return None
    return OddsApiProvider(key)


def _resolve_leagues(config: AppConfig, league: str | None) -> list[str]:
    mapping = {
        "NFL": config.leagues.nfl_key,
        "CFB": config.leagues.cfb_key,
        "UFC": config.leagues.ufc_key or "ufc",
    }
    if league:
        return [mapping[league]]
    return [mapping["NFL"], mapping["CFB"], mapping["UFC"]]


def _league_suffix(league_key: str) -> str:
    if "nfl" in league_key:
        return "nfl"
    if "ncaaf" in league_key:
        return "cfb"
    if "ufc" in league_key or "mma" in league_key:
        return "ufc"
    return league_key.replace("/", "_")


def _to_json(value: Any) -> str:
    return json.dumps(value, default=_json_default, indent=2)


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Type not serializable: {type(value)!r}")
