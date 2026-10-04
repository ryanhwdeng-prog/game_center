from __future__ import annotations

import json
import math
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DATABASE_PATH = ROOT / "amazon_cart_scores.sqlite3"
MAX_REQUEST_BYTES = 8192


def connect_database(database_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE IF NOT EXISTS shopping_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            seconds INTEGER NOT NULL CHECK(seconds >= 0),
            score INTEGER NOT NULL CHECK(score >= 0),
            item_count INTEGER NOT NULL CHECK(item_count >= 0),
            savings REAL NOT NULL CHECK(savings >= 0),
            total REAL NOT NULL CHECK(total >= 0),
            created_at TEXT NOT NULL
        )"""
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_shopping_scores_fastest "
        "ON shopping_scores(seconds ASC, score DESC, id ASC)"
    )
    return connection


def fetch_scores(database_path: Path = DATABASE_PATH, limit: int = 100) -> list[dict]:
    with closing(connect_database(database_path)) as connection:
        rows = connection.execute(
            """SELECT id, name, seconds, score, item_count, savings, total, created_at
               FROM shopping_scores
               ORDER BY seconds ASC, score DESC, id ASC
               LIMIT ?""",
            (max(1, min(int(limit), 500)),),
        ).fetchall()
    return [dict(row) for row in rows]


def save_score(payload: object, database_path: Path = DATABASE_PATH) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")

    name = payload.get("name")
    seconds = payload.get("seconds")
    score = payload.get("score")
    item_count = payload.get("count")
    savings = payload.get("savings")
    total = payload.get("total")

    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 16:
        raise ValueError("Name must contain 1 to 16 characters")
    for label, value, maximum in (
        ("seconds", seconds, 86400),
        ("score", score, 10000000),
        ("count", item_count, 10000),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
            raise ValueError(f"{label} must be a valid non-negative integer")
    for label, value in (("savings", savings), ("total", total)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 10000000:
            raise ValueError(f"{label} must be a valid non-negative number")

    created_at = datetime.now(timezone.utc).isoformat()
    with closing(connect_database(database_path)) as connection:
        cursor = connection.execute(
            """INSERT INTO shopping_scores
               (name, seconds, score, item_count, savings, total, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name.strip(), seconds, score, item_count, savings, total, created_at),
        )
        row = connection.execute(
            """SELECT id, name, seconds, score, item_count, savings, total, created_at
               FROM shopping_scores WHERE id = ?""",
            (cursor.lastrowid,),
        ).fetchone()
        connection.commit()
    return dict(row)


class ScoresHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, status: int, data: object) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == f"/{DATABASE_PATH.name}":
            self.send_json(404, {"error": "Not found"})
            return
        if parsed.path != "/api/scores":
            super().do_GET()
            return
        query = parse_qs(parsed.query)
        try:
            limit = int(query.get("limit", ["100"])[0])
            self.send_json(200, {"scores": fetch_scores(limit=limit)})
        except (TypeError, ValueError):
            self.send_json(400, {"error": "Invalid score limit"})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/scores":
            self.send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > MAX_REQUEST_BYTES:
                raise ValueError("Invalid request size")
            payload = json.loads(self.rfile.read(length))
            score = save_score(payload)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
            self.send_json(400, {"error": str(error)})
            return
        except (OSError, sqlite3.Error):
            self.send_json(500, {"error": "Could not save score"})
            return
        self.send_json(201, {"score": score})


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), ScoresHandler)
    print(f"Game Center running at http://127.0.0.1:{server.server_port}")
    print(f"Scores database: {DATABASE_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Game Center")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()