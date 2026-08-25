"""Username + password accounts.
See server/app.py's process_request for where signup/login/token
verification actually get wired into the HTTP layer.
"""

import hashlib
import os
import re
import secrets
import sqlite3
import time

DB_PATH = os.environ.get(
    "VIM_CADDIE_PROGRESS_DB",
    os.path.join(os.path.expanduser("~"), ".cache", "vim-caddie", "progress.db"),
)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

_VALID_USERNAME = re.compile(r"^[a-z0-9_-]{3,32}$")
_PBKDF2_ITERATIONS = 260_000
SESSION_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days


class AuthError(Exception):
    """Message is safe to show the player as-is."""


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            created_at REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """
    )
    return conn


def _normalize(username):
    return (username or "").strip().lower()


def is_valid_username(username):
    return bool(_VALID_USERNAME.match(_normalize(username)))


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, _PBKDF2_ITERATIONS)


def sign_up(username, password):
    username = _normalize(username)
    if not is_valid_username(username):
        raise AuthError("Username must be 3-32 characters: lowercase letters, digits, _ or -.")
    if not password or len(password) < 6:
        raise AuthError("Password must be at least 6 characters.")
    salt = os.urandom(16)
    password_hash = _hash_password(password, salt)
    conn = _connect()
    try:
        try:
            with conn:
                conn.execute(
                    "INSERT INTO users (username, salt, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (username, salt, password_hash, time.time()),
                )
        except sqlite3.IntegrityError:
            # relying on the PRIMARY KEY constraint itself (not just a
            # SELECT-then-INSERT check) to close the race between two
            # concurrent signups for the same name
            raise AuthError("That username is already taken.")
        return _create_session(conn, username)
    finally:
        conn.close()


def log_in(username, password):
    username = _normalize(username)
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT salt, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            # deliberately the same message as a wrong password — telling
            # them "no such user" instead would let someone enumerate
            # which usernames exist
            raise AuthError("Invalid username or password.")
        salt, expected_hash = row
        actual_hash = _hash_password(password, salt)
        if not secrets.compare_digest(actual_hash, expected_hash):
            raise AuthError("Invalid username or password.")
        return _create_session(conn, username)
    finally:
        conn.close()


def _create_session(conn, username):
    token = secrets.token_urlsafe(32)
    with conn:
        conn.execute(
            "INSERT INTO sessions (token, username, created_at) VALUES (?, ?, ?)",
            (token, username, time.time()),
        )
    return token, username


def log_out(token):
    if not token:
        return
    conn = _connect()
    try:
        with conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    finally:
        conn.close()


def username_for_token(token):
    """None if the token is missing, unknown, or expired -- callers treat
    that the same as "not authenticated", not as an error on their part."""
    if not token:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT username, created_at FROM sessions WHERE token = ?", (token,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    username, created_at = row
    if time.time() - created_at > SESSION_TTL_SECONDS:
        return None
    return username
