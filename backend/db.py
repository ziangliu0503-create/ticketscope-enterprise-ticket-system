import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        database_path = Path(current_app.config["DATABASE"])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    schema_path = Path(__file__).with_name("schema.sql")
    db.executescript(schema_path.read_text(encoding="utf-8"))
    user_columns = {row["name"] for row in db.execute("PRAGMA table_info(users)").fetchall()}
    if "password_hash" not in user_columns:
        db.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    ticket_columns = {row["name"] for row in db.execute("PRAGMA table_info(tickets)").fetchall()}
    if "escalation_level" not in ticket_columns:
        db.execute("ALTER TABLE tickets ADD COLUMN escalation_level INTEGER NOT NULL DEFAULT 0")
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
