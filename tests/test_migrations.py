import sqlite3
import sys

import pytest


def test_ensure_db_adds_columns(tmp_path, monkeypatch):
    db = tmp_path / 'migrate.db'
    # create an older/simple items table without total_episodes and seasons
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE items (
            id INTEGER PRIMARY KEY,
            kind TEXT NOT NULL,
            name TEXT NOT NULL,
            season INTEGER,
            episode INTEGER,
            chapter INTEGER,
            notes TEXT,
            updated_at TEXT NOT NULL
        );
    ''')
    conn.commit(); conn.close()

    # point the module to this DB before importing
    monkeypatch.setenv('SHOWTRACKER_DB', str(db))
    # ensure a fresh import
    if 'showtracker' in sys.modules:
        del sys.modules['showtracker']
    import showtracker

    # call ensure_db which should add missing columns
    conn2 = showtracker.ensure_db()
    conn2.close()

    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    cur.execute('PRAGMA table_info(items)')
    cols = [r[1] for r in cur.fetchall()]
    conn.close()

    assert 'total_episodes' in cols, 'Migration should add total_episodes column'
    assert 'seasons' in cols, 'Migration should add seasons column'
