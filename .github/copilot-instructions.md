# ShowTracker Copilot Instructions

## Quick Start

- **Run tests:** `pytest` (all) or `pytest tests/test_parse_and_match.py -v` (single file)
- **Manual test:** `python3 showtracker.py add show "Test Show" S1E01`
- **Install locally:** `sudo install -Dm755 showtracker.py /usr/local/bin/showtracker`

## Architecture

ShowTracker is a **monolithic CLI tool** (single `showtracker.py` file) for tracking TV show progress and book chapters:

- **DB:** SQLite at `~/.local/share/showtracker.db` (or `$SHOWTRACKER_DB`). Schema: `items` table with `name` (case-insensitive unique), `kind` (show/book), `season`/`episode`/`chapter`, `updated_at`.
- **Parsing:** Regex-based progress matching in `parse_progress_tokens()` — handles "S1E2", "1 2", "c 5" formats.
- **CLI:** Subcommands (`add`, `set`, `list`, `show`, `rm`, `import-csv`, `export-csv`) + shorthand (`showtracker "Name"` increments, `"Name" ns` starts next season).
- **DB Migrations:** `ensure_db()` creates schema and adds missing columns; case-insensitive index created if SQLite supports it.

## Key Patterns

- **No dependencies:** Stdlib only (sqlite3, argparse, csv, json, re). Keep it that way.
- **Interactive input:** `ask_for_int()` for user prompts with optional defaults.
- **Error handling:** Fuzzy matching with `difflib` for typos; invalid progress raises exceptions.
- **DB transactions:** `conn.commit()` explicit; default `autocommit=False` in sqlite3.

## Testing

- `conftest.py` adds repo root to `sys.path` so test imports work.
- Tests use fixtures for isolated DB instances (check `conftest.py` for setup).
- `test_parse_and_match.py`: Covers progress parsing ("S1E2", "1x5", chapter formats).
- `test_migrations.py`: Validates schema creation and column additions.

## Common Tasks

- **Add a subcommand:** Define function like `def cmd_name(args):` in main module, add to `parse_args()` subparsers, then call from `main()`.
- **Modify DB schema:** Alter in `SCHEMA` string and add migration in `ensure_db()` (try/except for compatibility with old DBs).
- **Change progress format:** Update regexes (`RE_SEP_EP`, `RE_CH_SIMPLE`, `RE_CH_NUM`) and add test case.
