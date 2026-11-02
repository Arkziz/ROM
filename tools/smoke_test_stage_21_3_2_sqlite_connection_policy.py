#!/usr/bin/env python3
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.sqlite_connection_policy import connect_runtime

with tempfile.TemporaryDirectory(prefix="rom_stage_21_3_2_") as temporary:
    path = Path(temporary) / "policy.sqlite3"
    connection = connect_runtime(path)
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 30000
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 0
        connection.execute("CREATE TABLE parent(id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE child(parent_id INTEGER REFERENCES parent(id))")
        try:
            connection.execute("INSERT INTO child(parent_id) VALUES (999)")
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("foreign key policy not enforced")
    finally:
        connection.close()

    read_only = connect_runtime(path, query_only=True)
    try:
        assert read_only.execute("PRAGMA query_only").fetchone()[0] == 1
        try:
            read_only.execute("CREATE TABLE forbidden(id INTEGER)")
        except sqlite3.OperationalError:
            pass
        else:
            raise AssertionError("query_only policy not enforced")
    finally:
        read_only.close()

print("PASS: Stage 21.3.2 isolated SQLite connection policy smoke")
