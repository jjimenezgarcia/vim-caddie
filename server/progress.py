"""Per-account progress tracking. A "user" here is a real username +
password account (see server/auth.py) — this module's whole job is
"given this username, what has it holed out, and what's the best stroke
count it did it in." Callers only ever pass a username that auth.py has
already resolved from a verified session token, never one taken directly
off the wire — this module isn't the trust boundary, auth.py is.
"""

import os
import sqlite3
import time

DB_PATH = os.environ.get(
    "VIM_CADDIE_PROGRESS_DB",
    os.path.join(os.path.expanduser("~"), ".cache", "vim-caddie", "progress.db"),
)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            username TEXT NOT NULL,
            exercise_id TEXT NOT NULL,
            best_strokes INTEGER,
            first_holed_at REAL NOT NULL,
            last_holed_at REAL NOT NULL,
            PRIMARY KEY (username, exercise_id)
        )
        """
    )
    return conn


def record_hole_out(username, exercise_id, strokes):
    """strokes: total real keystrokes the session counted, or None for
    exercises with no fixed reference path (reach_markers) where a stroke
    count isn't a meaningful thing to compare across attempts. Keeps
    whichever attempt was BEST across repeats, not just the latest —
    first_holed_at stays fixed at the first-ever completion. username is
    None for an unauthenticated session (no token, or an expired/unknown
    one) — a no-op, not an error, same as before login existed at all."""
    if not username:
        return
    now = time.time()
    conn = _connect()
    try:
        with conn:
            existing = conn.execute(
                "SELECT best_strokes FROM progress WHERE username = ? AND exercise_id = ?",
                (username, exercise_id),
            ).fetchone()
            if existing is None:
                conn.execute(
                    "INSERT INTO progress (username, exercise_id, best_strokes, first_holed_at, last_holed_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (username, exercise_id, strokes, now, now),
                )
            else:
                (prev_best,) = existing
                new_best = strokes if (strokes is not None and (prev_best is None or strokes < prev_best)) else prev_best
                conn.execute(
                    "UPDATE progress SET best_strokes = ?, last_holed_at = ? WHERE username = ? AND exercise_id = ?",
                    (new_best, now, username, exercise_id),
                )
    finally:
        conn.close()


def get_progress(username):
    if not username:
        return {}
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT exercise_id, best_strokes, first_holed_at, last_holed_at FROM progress WHERE username = ?",
            (username,),
        ).fetchall()
    finally:
        conn.close()
    return {
        exercise_id: {
            "holed": True,
            "best_strokes": best_strokes,
            "first_holed_at": first_holed_at,
            "last_holed_at": last_holed_at,
        }
        for exercise_id, best_strokes, first_holed_at, last_holed_at in rows
    }
