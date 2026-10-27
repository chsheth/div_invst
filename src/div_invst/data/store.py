"""SQLite snapshot store for fetched data.

Every fetch is appended to `raw` with its timestamp and never overwritten, so each run leaves a snapshot (yfinance
revisions and analyst data are point-in-time and cannot be re-fetched later). Readers take the newest row for a
(source, kind, ticker), optionally only when it is younger than `max_age_days`. Market-wide series (FRED) use an empty
ticker. Payloads are JSON.
"""
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[3] / "data" / "cache" / "div_invst.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    kind TEXT NOT NULL,
    ticker TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS raw_lookup ON raw (source, kind, ticker, fetched_at);
"""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Store:
    def __init__(self, path: Path | str = DEFAULT_DB):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.executescript(SCHEMA)

    def put(self, source: str, kind: str, ticker: str, payload, now: datetime | None = None) -> None:
        self.db.execute("INSERT INTO raw (source, kind, ticker, fetched_at, payload) VALUES (?, ?, ?, ?, ?)",
                        (source, kind, ticker, (now or utcnow()).isoformat(), json.dumps(payload, default=str)))
        self.db.commit()

    def latest(self, source: str, kind: str, ticker: str = "", max_age_days: float | None = None,
               now: datetime | None = None):
        """(fetched_at, payload) of the newest matching row, or None when absent or older than max_age_days."""
        row = self.db.execute("SELECT fetched_at, payload FROM raw WHERE source = ? AND kind = ? AND ticker = ? "
                              "ORDER BY fetched_at DESC, id DESC LIMIT 1", (source, kind, ticker)).fetchone()
        if row is None:
            return None
        fetched = datetime.fromisoformat(row[0])
        if max_age_days is not None and (now or utcnow()) - fetched > timedelta(days=max_age_days):
            return None
        return fetched, json.loads(row[1])

    def history(self, source: str, kind: str, ticker: str = "") -> list[tuple[datetime, object]]:
        """All snapshots, oldest first."""
        rows = self.db.execute("SELECT fetched_at, payload FROM raw WHERE source = ? AND kind = ? AND ticker = ? "
                               "ORDER BY fetched_at, id", (source, kind, ticker)).fetchall()
        return [(datetime.fromisoformat(f), json.loads(p)) for f, p in rows]

    def tickers(self, kind: str) -> set[str]:
        """Tickers that have at least one snapshot of `kind`."""
        return {r[0] for r in self.db.execute("SELECT DISTINCT ticker FROM raw WHERE kind = ?", (kind,))}

    def close(self) -> None:
        self.db.close()
