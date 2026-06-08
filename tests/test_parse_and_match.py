import sqlite3
import os
from datetime import datetime

import pytest

from showtracker import parse_progress_tokens, find_matches, SCHEMA


def test_parse_progress_tokens():
    assert parse_progress_tokens(None) == (None, None, None)
    assert parse_progress_tokens('') == (None, None, None)
    assert parse_progress_tokens('S3E05') == (3, 5, None)
    assert parse_progress_tokens('s1e2') == (1, 2, None)
    assert parse_progress_tokens('c12') == (None, None, 12)
    assert parse_progress_tokens('12') == (None, 12, None)


def test_find_matches_partial_and_fuzzy(tmp_path):
    db_path = tmp_path / 'fm.db'
    conn = sqlite3.connect(str(db_path))
    # use schema from module to create table with expected columns
    conn.executescript(SCHEMA)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        INSERT INTO items(kind,name,season,episode,chapter,total_episodes,seasons,notes,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?)
    """, ('show', 'Stranger Things', 1, 2, None, None, None, None, now))
    cur.execute("""
        INSERT INTO items(kind,name,season,episode,chapter,total_episodes,seasons,notes,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?)
    """, ('book', 'The Hobbit', None, None, 12, None, None, None, now))
    cur.execute("""
        INSERT INTO items(kind,name,season,episode,chapter,total_episodes,seasons,notes,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?)
    """, ('show', 'Stranger Tales', 2, 1, None, None, None, None, now))
    conn.commit()

    # partial match should find both Stranger entries
    res = find_matches(conn, 'Stranger')
    assert any('Stranger Things' == r[2] for r in res)
    assert any('Stranger Tales' == r[2] for r in res)

    # fuzzy match for misspelled name should return the intended name
    res2 = find_matches(conn, 'Strnger Thngs')
    assert res2 and res2[0][2] == 'Stranger Things'

    conn.close()
