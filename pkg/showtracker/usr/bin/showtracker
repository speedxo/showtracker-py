#!/usr/bin/env python3
"""
showtracker.py - CLI to track TV shows (season/episode) and books (chapter)

Shorthand (no subcommand):
  showtracker.py "Name"        # increment episode/chapter
  showtracker.py "Name" 5      # set episode/chapter to 5 (within current season)
  showtracker.py "Name" ns     # start next season for shows

Subcommands: add, set, list, show, rm, import-csv, export-csv

DB: ~/.local/share/showtracker.db (override with SHOWTRACKER_DB)
"""

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
import difflib

DB_PATH = os.getenv("SHOWTRACKER_DB") or os.path.join(os.path.expanduser("~"), ".local", "share", "showtracker.db")
SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    season INTEGER,
    episode INTEGER,
    chapter INTEGER,
    total_episodes INTEGER,
    seasons TEXT,
    notes TEXT,
    updated_at TEXT NOT NULL
);
"""

RE_SEP_EP = re.compile(r"(?i)S?(?P<season>\d+)[x: ]?E?(?P<episode>\d+)")
RE_CH_SIMPLE = re.compile(r"(?i)c\s*(?P<chapter>\d+)")
RE_CH_NUM = re.compile(r"(?<!\d)(?P<num>\d+)(?!\d)")


def ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    # add missing columns if database existed before
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(items)")
    cols = {r[1] for r in cur.fetchall()}  # name is column 1
    if 'total_episodes' not in cols:
        try:
            cur.execute("ALTER TABLE items ADD COLUMN total_episodes INTEGER")
        except Exception:
            pass
    if 'seasons' not in cols:
        try:
            cur.execute("ALTER TABLE items ADD COLUMN seasons TEXT")
        except Exception:
            pass
    # ensure case-insensitive uniqueness on name (expression index may not be available on very old SQLite)
    try:
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_items_name_lower ON items(LOWER(name));")
    except Exception:
        # ignore if not supported
        pass
    conn.commit()
    return conn


def parse_progress_tokens(text):
    if not text:
        return None, None, None
    parts = text if isinstance(text, (list, tuple)) else text.split()
    joined = " ".join(parts)
    low = joined.lower()
    # If it looks explicitly like a season/episode (contains 's' or 'e' or 'x' or a non-digit separator between numbers), prefer that
    if re.search(r'(?i)[se]|x', joined) or re.search(r'\d+\D+\d+', joined):
        m = RE_SEP_EP.search(joined)
        if m:
            return int(m.group('season')), int(m.group('episode')), None
    # If it looks explicitly like a chapter token, parse chapter
    if 'c' in low or 'chapter' in low or re.search(r'(?i)\bch\b', joined):
        m = RE_CH_SIMPLE.search(joined)
        if m:
            return None, None, int(m.group('chapter'))
    # If it's just a number, treat as episode within current season
    if re.fullmatch(r"\d+", joined.strip()):
        return None, int(joined.strip()), None
    # fallback: try s/e pattern then chapter
    m = RE_SEP_EP.search(joined)
    if m:
        return int(m.group('season')), int(m.group('episode')), None
    m = RE_CH_SIMPLE.search(joined)
    if m:
        return None, None, int(m.group('chapter'))
    return None, None, None


from difflib import SequenceMatcher

def find_matches(conn, name, limit=10):
    cur = conn.cursor()
    cur.execute("SELECT id, kind, name, season, episode, chapter FROM items ORDER BY name")
    rows = cur.fetchall()
    names = [r[2] for r in rows]
    # partial matches first (substring)
    lower = name.lower()
    partials = [r for r in rows if lower in (r[2] or '').lower()]
    if partials:
        return partials[:limit]
    # fuzzy matches using difflib; sort by similarity score to prefer the best match
    choices = difflib.get_close_matches(name, names, n=limit, cutoff=0.2)
    if not choices:
        return []
    # compute similarity and sort
    scored = []
    for r in rows:
        if r[2] in choices:
            score = SequenceMatcher(None, name.lower(), (r[2] or '').lower()).ratio()
            scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [r for _, r in scored][:limit]
    return results


def ask_for_int(label, default=None):
    while True:
        try:
            v = input(f"{label} [{default}]: ")
        except EOFError:
            return default
        v = v.strip()
        if not v:
            return default
        try:
            return int(v)
        except ValueError:
            print("Please enter a number.")


def print_record(row):
    kind = row['kind']
    if kind == 'show':
        te = row['total_episodes']
        te_str = f" / {te}" if te else ""
        print(f"{row['name']} - S{row['season']}E{row['episode']}{te_str}  (notes: {row['notes'] or '-'})")
        # seasons JSON can hold per-season notes or metadata
        seasons = row['seasons']
        if seasons:
            try:
                sdata = json.loads(seasons)
                if isinstance(sdata, dict) and str(row['season']) in sdata:
                    print(f"  season notes: {sdata[str(row['season'])]}")
            except Exception:
                pass
    else:
        print(f"{row['name']} - C{row['chapter']}  (notes: {row['notes'] or '-'})")


def add_item(args):
    conn = ensure_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    kind = args.kind
    name = args.name
    s = e = c = None
    te = getattr(args, 'total_episodes', None)
    seasons_json = getattr(args, 'seasons', None)
    if getattr(args, 'progress', None):
        s, e, c = parse_progress_tokens(args.progress)
    if kind == 'show' and (s is None or e is None):
        if s is None: s = ask_for_int('Season', default=1)
        if e is None: e = ask_for_int('Episode', default=1)
    if kind == 'book' and c is None:
        c = ask_for_int('Chapter', default=1)
    now = datetime.utcnow().isoformat()
    try:
        cur.execute("INSERT INTO items(kind,name,season,episode,chapter,total_episodes,seasons,notes,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                    (kind, name, s, e, c, te, seasons_json, args.notes, now))
        conn.commit()
        print('Saved.')
    except sqlite3.IntegrityError:
        print('An item with this (case-insensitive) name already exists. Use set to update.')
    finally:
        conn.close()


def set_item(args):
    conn = ensure_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    name = args.name
    cur.execute("SELECT id, kind, name, season, episode, chapter, total_episodes, seasons FROM items WHERE LOWER(name)=?", (name.lower(),))
    row = cur.fetchone()
    if not row:
        print('No such item. Use add to create it.')
        conn.close(); return
    _id, kind, _, season, episode, chapter, total_episodes, seasons = row
    s = e = c = None
    if getattr(args, 'progress', None):
        s, e, c = parse_progress_tokens(args.progress)
    if args.season is not None: s = args.season
    if args.episode is not None: e = args.episode
    if args.chapter is not None: c = args.chapter
    if args.total_episodes is not None: total_episodes = args.total_episodes
    if getattr(args, 'seasons', None) is not None: seasons = args.seasons
    if kind == 'show' and s is None and e is None:
        s = ask_for_int('Season', default=season or 1)
        e = ask_for_int('Episode', default=episode or 1)
    if kind == 'book' and c is None:
        c = ask_for_int('Chapter', default=chapter or 1)
    now = datetime.utcnow().isoformat()
    cur.execute("UPDATE items SET season=?,episode=?,chapter=?,total_episodes=?,seasons=?,notes=?,updated_at=? WHERE id=?",
                (s or season, e or episode, c or chapter, total_episodes, seasons, args.notes, now, _id))
    conn.commit(); conn.close(); print('Updated.')


def export_csv(args):
    conn = ensure_db(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    cur.execute("SELECT kind,name,season,episode,chapter,total_episodes,seasons,notes,updated_at FROM items ORDER BY kind,name")
    rows = cur.fetchall()
    outpath = args.path
    fieldnames = ['kind','name','season','episode','chapter','total_episodes','seasons','notes','updated_at']
    if outpath == '-':
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})
        conn.close(); return
    with open(outpath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})
    conn.close(); print(f'Exported {len(rows)} rows to {outpath}')


def import_csv(args):
    path = args.path
    if not os.path.exists(path):
        print('File not found:', path); return
    conn = ensure_db(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    fieldnames = ['kind','name','season','episode','chapter','total_episodes','seasons','notes','updated_at']
    added = updated = 0
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            kind = row['kind'] or 'show'
            name = row['name']
            if not name:
                continue
            # normalize numeric fields
            def to_int(v):
                try:
                    return int(v) if v not in (None,'') else None
                except Exception:
                    return None
            season = to_int(row['season'])
            episode = to_int(row['episode'])
            chapter = to_int(row['chapter'])
            total_episodes = to_int(row['total_episodes'])
            seasons = row['seasons']
            notes = row['notes']
            updated_at = row['updated_at'] or datetime.utcnow().isoformat()
            # upsert by case-insensitive name
            cur.execute("SELECT id FROM items WHERE LOWER(name)=?", (name.lower(),))
            existing = cur.fetchone()
            if existing:
                cur.execute("UPDATE items SET kind=?,season=?,episode=?,chapter=?,total_episodes=?,seasons=?,notes=?,updated_at=? WHERE id=?",
                            (kind, season, episode, chapter, total_episodes, seasons, notes, updated_at, existing[0]))
                updated += 1
            else:
                try:
                    cur.execute("INSERT INTO items(kind,name,season,episode,chapter,total_episodes,seasons,notes,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                                (kind, name, season, episode, chapter, total_episodes, seasons, notes, updated_at))
                    added += 1
                except sqlite3.IntegrityError:
                    updated += 1
    conn.commit(); conn.close(); print(f'Imported: {added} added, {updated} updated')


def shorthand_progress(name, prog, new_season_flag=False):
    conn = ensure_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, kind, name, season, episode, chapter, notes, total_episodes, seasons FROM items WHERE LOWER(name)=?", (name.lower(),))
    row = cur.fetchone()
    if not row:
        matches = find_matches(conn, name)
        if matches:
            print('No exact match. Fuzzy matches:')
            for i, (mid, kind, mname, season, episode, chapter) in enumerate(matches, start=1):
                if kind == 'show':
                    print(f"{i}. [show] {mname} - S{season or '?'}E{episode or '?'}")
                else:
                    print(f"{i}. [book] {mname} - C{chapter or '?'}")
            choice = input("Choose number to update, 'a' to add, or Enter to cancel: ").strip()
            if choice == '': print('Cancelled.'); conn.close(); return
            if choice.lower().startswith('a'):
                # interactive add
                k = input('Is this a (s)how or (b)ook? [s]: ').strip().lower() or 's'
                kind = 'show' if k.startswith('s') else 'book'
                s = e = c = None
                if prog: s,e,c = parse_progress_tokens(prog)
                if kind=='show':
                    if s is None: s = ask_for_int('Season', default=1)
                    if e is None: e = ask_for_int('Episode', default=1)
                else:
                    if c is None: c = ask_for_int('Chapter', default=1)
                now = datetime.utcnow().isoformat()
                try:
                    cur.execute("INSERT INTO items(kind,name,season,episode,chapter,notes,updated_at) VALUES(?,?,?,?,?,?,?)",
                                (kind, name, s, e, c, None, now))
                    conn.commit(); print('Added.'); conn.close(); return
                except sqlite3.IntegrityError:
                    print('Name already exists (case-insensitive).'); conn.close(); return
            try:
                idx = int(choice)-1; sel = matches[idx]
            except Exception:
                print('Invalid choice.'); conn.close(); return
            cur.execute("SELECT id, kind, name, season, episode, chapter, notes, total_episodes, seasons FROM items WHERE id=?", (sel[0],))
            row = cur.fetchone()
            if not row: print('Unexpected error.'); conn.close(); return
        else:
            yn = input(f'"{name}" not found. Add new? [y/N]: ').strip().lower()
            if yn != 'y': print('Cancelled.'); conn.close(); return
            k = input('Is this a (s)how or (b)ook? [s]: ').strip().lower() or 's'
            kind = 'show' if k.startswith('s') else 'book'
            s = e = c = None
            if prog: s,e,c = parse_progress_tokens(prog)
            if kind=='show':
                if s is None: s = ask_for_int('Season', default=1)
                if e is None: e = ask_for_int('Episode', default=1)
            else:
                if c is None: c = ask_for_int('Chapter', default=1)
            now = datetime.utcnow().isoformat()
            try:
                cur.execute("INSERT INTO items(kind,name,season,episode,chapter,notes,updated_at) VALUES(?,?,?,?,?,?,?)",
                            (kind, name, s, e, c, None, now))
                conn.commit(); print('Added.'); conn.close(); return
            except sqlite3.IntegrityError:
                print('Name already exists (case-insensitive).'); conn.close(); return

    # now row exists
    _id = row['id']; kind = row['kind']; season = row['season']; episode = row['episode']; chapter = row['chapter']; notes = row['notes']; total_episodes = row['total_episodes']; seasons = row['seasons']
    s = e = c = None
    if prog: s,e,c = parse_progress_tokens(prog)
    # new season flag
    if prog and prog.strip().lower() in ('ns','s+','newseason','new-season','n'):
        new_season_flag = True
    now = datetime.utcnow().isoformat()
    if kind == 'show':
        if new_season_flag:
            season = (season or 0) + 1
            episode = 1
        elif s is not None and e is not None:
            season, episode = s, e
        elif e is not None:
            episode = e
        elif s is not None:
            season = s
        else:
            episode = (episode or 0) + 1
        cur.execute("UPDATE items SET season=?,episode=?,updated_at=? WHERE id=?", (season, episode, now, _id))
    else:
        if c is not None:
            chapter = c
        else:
            chapter = (chapter or 0) + 1
        cur.execute("UPDATE items SET chapter=?,updated_at=? WHERE id=?", (chapter, now, _id))
    conn.commit()

    # show record and offer edit
    cur.execute("SELECT id, kind, name, season, episode, chapter, notes, total_episodes, seasons FROM items WHERE id=?", (_id,))
    row = cur.fetchone()
    print_record(row)
    choice = input("Press Enter to dismiss, type 'e' to edit: ").strip().lower()
    if choice == 'e':
        if kind == 'show':
            season = ask_for_int('Season', default=season)
            episode = ask_for_int('Episode', default=episode)
            notes = input('Notes (empty to keep): ').strip() or notes
            now = datetime.utcnow().isoformat()
            cur.execute("UPDATE items SET season=?,episode=?,notes=?,updated_at=? WHERE id=?", (season, episode, notes, now, _id))
            conn.commit(); cur.execute("SELECT id, kind, name, season, episode, chapter, notes FROM items WHERE id=?", (_id,)); print_record(cur.fetchone())
        else:
            chapter = ask_for_int('Chapter', default=chapter)
            notes = input('Notes (empty to keep): ').strip() or notes
            now = datetime.utcnow().isoformat()
            cur.execute("UPDATE items SET chapter=?,notes=?,updated_at=? WHERE id=?", (chapter, notes, now, _id))
            conn.commit(); cur.execute("SELECT id, kind, name, season, episode, chapter, notes FROM items WHERE id=?", (_id,)); print_record(cur.fetchone())

    conn.close()


def list_items(args):
    conn = ensure_db(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    cur.execute("SELECT kind,name,season,episode,chapter,total_episodes,updated_at FROM items ORDER BY kind,name")
    rows = cur.fetchall()
    if not rows:
        print('No items tracked yet.')
    else:
        for r in rows:
            if r['kind']=='show':
                te = r['total_episodes']
                te_str = f"/{te}" if te else ""
                print(f"[show] {r['name']} - S{r['season'] or '?'}E{r['episode'] or '?'} {te_str} (updated {r['updated_at']})")
            else:
                print(f"[book] {r['name']} - C{r['chapter'] or '?'} (updated {r['updated_at']})")
    conn.close()


def show_item(args):
    conn = ensure_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT kind,name,season,episode,chapter,total_episodes,seasons,notes,updated_at FROM items WHERE LOWER(name)=?", (args.name.lower(),))
    row = cur.fetchone()
    if row:
        print_record(row)
        print(f"updated: {row['updated_at']}")
        conn.close()
        return

    matches = find_matches(conn, args.name)
    if not matches:
        yn = input(f'"{args.name}" not found. Add new? [y/N]: ').strip().lower()
        if yn != 'y':
            print('Not found.')
            conn.close()
            return
        k = input('Is this a (s)how or (b)ook? [s]: ').strip().lower() or 's'
        kind = 'show' if k.startswith('s') else 'book'
        prog = getattr(args, 'progress', None)
        s = e = c = None
        if prog:
            s, e, c = parse_progress_tokens(prog)
        if kind == 'show':
            if s is None:
                s = ask_for_int('Season', default=1)
            if e is None:
                e = ask_for_int('Episode', default=1)
        else:
            if c is None:
                c = ask_for_int('Chapter', default=1)
        now = datetime.utcnow().isoformat()
        try:
            cur.execute("INSERT INTO items(kind,name,season,episode,chapter,notes,updated_at) VALUES(?,?,?,?,?,?,?)",
                        (kind, args.name, s, e, c, None, now))
            conn.commit()
            print('Added.')
        except sqlite3.IntegrityError:
            print('Name already exists.')
        conn.close()
        return

    # present fuzzy matches
    print('No exact match. Fuzzy matches:')
    for i, (mid, kind, mname, season, episode, chapter) in enumerate(matches, start=1):
        if kind == 'show':
            print(f"{i}. [show] {mname} - S{season or '?'}E{episode or '?'}")
        else:
            print(f"{i}. [book] {mname} - C{chapter or '?'}")
    choice = input("Choose number to show, 'a' to add new, or Enter to cancel: ").strip()
    if choice == '':
        print('Cancelled.')
        conn.close()
        return
    if choice.lower().startswith('a'):
        k = input('Is this a (s)how or (b)ook? [s]: ').strip().lower() or 's'
        kind = 'show' if k.startswith('s') else 'book'
        s = e = c = None
        prog = getattr(args, 'progress', None)
        if prog:
            s, e, c = parse_progress_tokens(prog)
        if kind == 'show':
            if s is None:
                s = ask_for_int('Season', default=1)
            if e is None:
                e = ask_for_int('Episode', default=1)
        else:
            if c is None:
                c = ask_for_int('Chapter', default=1)
        now = datetime.utcnow().isoformat()
        try:
            cur.execute("INSERT INTO items(kind,name,season,episode,chapter,notes,updated_at) VALUES(?,?,?,?,?,?,?)",
                        (kind, args.name, s, e, c, None, now))
            conn.commit()
            print('Added.')
        except sqlite3.IntegrityError:
            print('Name already exists.')
        conn.close()
        return
    try:
        idx = int(choice) - 1
        sel = matches[idx]
    except Exception:
        print('Invalid choice.')
        conn.close()
        return
    cur.execute("SELECT kind,name,season,episode,chapter,total_episodes,seasons,notes,updated_at FROM items WHERE id=?", (sel[0],))
    row = cur.fetchone()
    if not row:
        print('Unexpected error.')
        conn.close()
        return
    print_record(row)
    print(f"updated: {row['updated_at']}")
    conn.close()


def remove_item(args):
    conn = ensure_db(); cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE name=? COLLATE NOCASE", (args.name,))
    conn.commit(); print('Removed.' if cur.rowcount else 'No such item.'); conn.close()


def parse_args(argv):
    p = argparse.ArgumentParser(prog='showtracker')
    sub = p.add_subparsers(dest='cmd')
    p_add = sub.add_parser('add'); p_add.add_argument('kind', choices=['show','book']); p_add.add_argument('name'); p_add.add_argument('progress', nargs='*'); p_add.add_argument('--notes','-n',default=None); p_add.add_argument('--total-episodes',type=int,default=None); p_add.add_argument('--seasons',default=None,help='JSON blob for per-season metadata'); p_add.set_defaults(func=add_item)
    p_set = sub.add_parser('set'); p_set.add_argument('name'); p_set.add_argument('progress', nargs='*'); p_set.add_argument('--season',type=int); p_set.add_argument('--episode',type=int); p_set.add_argument('--chapter',type=int); p_set.add_argument('--notes','-n',default=None); p_set.add_argument('--total-episodes',type=int,default=None); p_set.add_argument('--seasons',default=None); p_set.set_defaults(func=set_item)
    p_list = sub.add_parser('list'); p_list.set_defaults(func=list_items)
    p_show = sub.add_parser('show'); p_show.add_argument('name'); p_show.set_defaults(func=show_item)
    p_rm = sub.add_parser('rm'); p_rm.add_argument('name'); p_rm.set_defaults(func=remove_item)
    p_export = sub.add_parser('export-csv'); p_export.add_argument('path', nargs='?', default='-'); p_export.set_defaults(func=export_csv)
    p_import = sub.add_parser('import-csv'); p_import.add_argument('path'); p_import.set_defaults(func=import_csv)

    if not argv: p.print_help(); sys.exit(0)
    known = {'add','set','list','show','rm','export-csv','import-csv'}
    if argv and argv[0] not in known:
        name = argv[0]
        prog = ' '.join(argv[1:]) if len(argv)>1 else None
        ns_flag = False
        if prog and prog.strip().lower() in ('ns','s+','newseason','new-season','n'): ns_flag = True
        class A: pass
        a = A(); a.name = name; a.progress = prog; a.new_season = ns_flag; a.func = lambda args=None: shorthand_progress(a.name, a.progress, a.new_season)
        return a
    args = p.parse_args(argv)
    if hasattr(args,'progress') and isinstance(args.progress,list): args.progress = ' '.join(args.progress) if args.progress else None
    return args


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if not hasattr(args,'func'):
        print('No command provided.'); return
    args.func(args)

if __name__ == '__main__':
    main()
