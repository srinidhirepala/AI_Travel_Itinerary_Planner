"""
Database layer — SQLite via sqlite3 (stdlib, no extra deps).
Handles users, profile interests, liked places, and saved itineraries.
"""
import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "travel.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    with _conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          TEXT PRIMARY KEY,   -- Google sub
            email       TEXT UNIQUE NOT NULL,
            name        TEXT,
            picture     TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS profiles (
            user_id         TEXT PRIMARY KEY REFERENCES users(id),
            food_pref       TEXT DEFAULT 'Vegetarian',
            interests       TEXT DEFAULT '[]',   -- JSON list
            home_city       TEXT DEFAULT '',
            travel_style    TEXT DEFAULT 'Explorer',
            budget_default  INTEGER DEFAULT 2000,
            updated_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS liked_places (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT REFERENCES users(id),
            place_name  TEXT NOT NULL,
            place_type  TEXT,               -- city / attraction / restaurant
            country     TEXT,
            notes       TEXT,
            saved_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS itineraries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT REFERENCES users(id),
            destination TEXT NOT NULL,
            days        INTEGER,
            budget      INTEGER,
            food_pref   TEXT,
            interests   TEXT,               -- JSON list
            data        TEXT NOT NULL,      -- full JSON blob from LLM
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS city_coordinates (
            city_name   TEXT PRIMARY KEY,
            latitude    REAL NOT NULL,
            longitude   REAL NOT NULL,
            cached_at   TEXT DEFAULT (datetime('now'))
        );
        """)

        # Lightweight migration for existing DBs created before budget_default existed
        profile_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(profiles)").fetchall()
        }
        if "budget_default" not in profile_cols:
            conn.execute("ALTER TABLE profiles ADD COLUMN budget_default INTEGER DEFAULT 2000")


# ── Users ─────────────────────────────────────────────────────────────────────

def upsert_user(sub: str, email: str, name: str, picture: str) -> None:
    with _conn() as conn:
        conn.execute("""
            INSERT INTO users (id, email, name, picture)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name, picture=excluded.picture
        """, (sub, email, name, picture))
        # Create default profile if first login
        conn.execute("""
            INSERT OR IGNORE INTO profiles (user_id) VALUES (?)
        """, (sub,))


def get_user(sub: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (sub,)).fetchone()
        return dict(row) if row else None


# ── Profile ───────────────────────────────────────────────────────────────────

def get_profile(user_id: str) -> Dict[str, Any]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            return {"user_id": user_id, "food_pref": "Vegetarian",
                    "interests": [], "home_city": "", "travel_style": "Explorer", "budget_default": 2000}
        d = dict(row)
        d["interests"] = json.loads(d.get("interests") or "[]")
        d["budget_default"] = int(d.get("budget_default") or 2000)
        return d


def save_profile(user_id: str, food_pref: str, interests: list,
                 home_city: str, travel_style: str, budget_default: int = 2000):
    with _conn() as conn:
        conn.execute("""
            INSERT INTO profiles (user_id, food_pref, interests, home_city, travel_style, budget_default, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                food_pref=excluded.food_pref,
                interests=excluded.interests,
                home_city=excluded.home_city,
                travel_style=excluded.travel_style,
                budget_default=excluded.budget_default,
                updated_at=excluded.updated_at
        """, (user_id, food_pref, json.dumps(interests), home_city, travel_style, budget_default))


# ── Liked places ──────────────────────────────────────────────────────────────

def add_liked_place(user_id: str, place_name: str, place_type: str,
                    country: str, notes: str = ""):
    with _conn() as conn:
        conn.execute("""
            INSERT INTO liked_places (user_id, place_name, place_type, country, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, place_name, place_type, country, notes))


def get_liked_places(user_id: str) -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM liked_places WHERE user_id=? ORDER BY saved_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def delete_liked_place(place_id: int):
    with _conn() as conn:
        conn.execute("DELETE FROM liked_places WHERE id=?", (place_id,))


# ── Itineraries ───────────────────────────────────────────────────────────────

def save_itinerary(user_id: str, destination: str, days: int, budget: int,
                   food_pref: str, interests: list, data: dict) -> int:
    with _conn() as conn:
        cur = conn.execute("""
            INSERT INTO itineraries (user_id, destination, days, budget, food_pref, interests, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, destination, days, budget, food_pref,
              json.dumps(interests), json.dumps(data)))
        return cur.lastrowid


def get_itineraries(user_id: str) -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, destination, days, budget, food_pref, interests, created_at FROM itineraries "
            "WHERE user_id=? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["interests"] = json.loads(d.get("interests") or "[]")
            result.append(d)
        return result


def get_itinerary_data(itin_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        row = conn.execute("SELECT data FROM itineraries WHERE id=?", (itin_id,)).fetchone()
        return json.loads(row["data"]) if row else None


def delete_itinerary(itin_id: int):
    with _conn() as conn:
        conn.execute("DELETE FROM itineraries WHERE id=?", (itin_id,))


# ── City coordinate cache ─────────────────────────────────────────────────────

def get_cached_coordinates(city_name: str):
    with _conn() as conn:
        row = conn.execute(
            "SELECT latitude, longitude FROM city_coordinates WHERE city_name=?",
            (city_name,)
        ).fetchone()
        return (row["latitude"], row["longitude"]) if row else None


def cache_coordinates(city_name: str, latitude: float, longitude: float):
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO city_coordinates (city_name, latitude, longitude) VALUES (?, ?, ?)",
            (city_name, latitude, longitude)
        )
