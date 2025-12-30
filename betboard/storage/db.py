from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from betboard.models import MovementEvent, OddsSnapshot, WatchlistItem


DEFAULT_DB_PATH = Path.home() / ".betboard" / "betboard.db"


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            event_id TEXT PRIMARY KEY,
            league_key TEXT NOT NULL,
            added_at TEXT NOT NULL,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS odds_snapshots (
            provider TEXT NOT NULL,
            league_key TEXT NOT NULL,
            market TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS movement_events (
            league_key TEXT NOT NULL,
            event_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            details_json TEXT NOT NULL
        );
        """
    )


def upsert_watchlist(conn: sqlite3.Connection, item: WatchlistItem) -> None:
    conn.execute(
        """
        INSERT INTO watchlist (event_id, league_key, added_at, notes)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(event_id) DO UPDATE SET
            league_key=excluded.league_key,
            added_at=excluded.added_at,
            notes=excluded.notes
        """,
        (item.event_id, item.league_key, item.added_at.isoformat(), item.notes),
    )
    conn.commit()


def remove_watchlist(conn: sqlite3.Connection, event_id: str) -> None:
    conn.execute("DELETE FROM watchlist WHERE event_id = ?", (event_id,))
    conn.commit()


def list_watchlist(conn: sqlite3.Connection) -> list[WatchlistItem]:
    rows = conn.execute("SELECT * FROM watchlist").fetchall()
    return [
        WatchlistItem(
            event_id=row["event_id"],
            league_key=row["league_key"],
            added_at=datetime.fromisoformat(row["added_at"]),
            notes=row["notes"],
        )
        for row in rows
    ]


def add_snapshot(conn: sqlite3.Connection, snapshot: OddsSnapshot) -> None:
    conn.execute(
        """
        INSERT INTO odds_snapshots (provider, league_key, market, fetched_at, payload_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            snapshot.provider,
            snapshot.league_key,
            snapshot.market,
            snapshot.fetched_at.isoformat(),
            json.dumps(snapshot.payload),
        ),
    )
    conn.commit()


def latest_snapshot(
    conn: sqlite3.Connection, provider: str, league_key: str, market: str
) -> OddsSnapshot | None:
    row = conn.execute(
        """
        SELECT * FROM odds_snapshots
        WHERE provider = ? AND league_key = ? AND market = ?
        ORDER BY fetched_at DESC
        LIMIT 1
        """,
        (provider, league_key, market),
    ).fetchone()
    if not row:
        return None
    return OddsSnapshot(
        provider=row["provider"],
        league_key=row["league_key"],
        market=row["market"],
        fetched_at=datetime.fromisoformat(row["fetched_at"]),
        payload=json.loads(row["payload_json"]),
    )


def add_movement(conn: sqlite3.Connection, movement: MovementEvent) -> None:
    conn.execute(
        """
        INSERT INTO movement_events (league_key, event_id, created_at, details_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            movement.league_key,
            movement.event_id,
            movement.created_at.isoformat(),
            json.dumps(movement.details),
        ),
    )
    conn.commit()


def list_movements(conn: sqlite3.Connection, league_key: str) -> list[MovementEvent]:
    rows = conn.execute(
        """
        SELECT * FROM movement_events
        WHERE league_key = ?
        ORDER BY created_at DESC
        LIMIT 100
        """,
        (league_key,),
    ).fetchall()
    return [
        MovementEvent(
            league_key=row["league_key"],
            event_id=row["event_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            details=json.loads(row["details_json"]),
        )
        for row in rows
    ]


def record_movement_events(
    conn: sqlite3.Connection, movements: list[MovementEvent]
) -> None:
    for movement in movements:
        add_movement(conn, movement)


def get_event_snapshot_payload(
    conn: sqlite3.Connection, provider: str, league_key: str, market: str
) -> dict[str, Any] | None:
    snapshot = latest_snapshot(conn, provider, league_key, market)
    if not snapshot:
        return None
    return snapshot.payload
