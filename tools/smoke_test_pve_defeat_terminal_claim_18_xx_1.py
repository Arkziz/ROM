#!/usr/bin/env python3
from __future__ import annotations
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import systems.pve_auto_escape_system as pve

class Bot:
    def __init__(self):
        self.user_data = {}
        self.messages = []
    def send_message(self, chat_id, text):
        self.messages.append((chat_id, text))


def iso(value):
    return value.astimezone(timezone.utc).isoformat()


with tempfile.TemporaryDirectory() as tmp:
    temp_db = Path(tmp) / "pve_terminal.sqlite3"
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    conn.executescript("""
    CREATE TABLE pve_encounters (
        encounter_id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        chat_id INTEGER NOT NULL,
        started_at TEXT NOT NULL,
        deadline_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        terminal_reason TEXT DEFAULT '',
        terminal_at TEXT,
        mob_snapshot_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE UNIQUE INDEX ux_pve_encounters_one_active_user
    ON pve_encounters(user_id) WHERE status='active';
    """)
    conn.commit()

    old_conn, old_cursor = pve.conn, pve.cursor
    pve.conn, pve.cursor = conn, cursor
    try:
        now = datetime(2026, 9, 15, 20, 0, tzinfo=timezone.utc)
        expired = now - timedelta(seconds=1)
        started = now - timedelta(minutes=5)
        bot = Bot()

        def add(encounter_id, user_id):
            conn.execute(
                "INSERT INTO pve_encounters VALUES (?,?,?,?,?,'active','',NULL,'{}',?,?)",
                (encounter_id, user_id, user_id, iso(started), iso(expired), iso(started), iso(started)),
            )
            conn.commit()

        add('defeat-1', 101)
        assert pve.claim_pve_terminal(101, 'defeat', 'defeat-1', now) is True
        assert pve.claim_pve_terminal(101, 'auto_escape', 'defeat-1', now, True) is False
        assert pve.expire_pve_encounters_once(bot, now) == []
        row = conn.execute("SELECT status,terminal_reason FROM pve_encounters WHERE encounter_id='defeat-1'").fetchone()
        assert dict(row) == {'status': 'defeat', 'terminal_reason': 'defeat'}
        assert bot.messages == []

        add('victory-1', 102)
        assert pve.claim_pve_terminal(102, 'victory', 'victory-1', now) is True
        assert pve.expire_pve_encounters_once(bot, now) == []

        add('manual-1', 103)
        assert pve.claim_pve_terminal(103, 'manual_escape', 'manual-1', now) is True
        assert pve.expire_pve_encounters_once(bot, now) == []

        add('expired-1', 104)
        claimed = pve.expire_pve_encounters_once(bot, now)
        assert len(claimed) == 1
        assert len(bot.messages) == 1
        assert pve.expire_pve_encounters_once(bot, now) == []
        assert len(bot.messages) == 1

        source = (ROOT / 'handlers/combat.py').read_text(encoding='utf-8-sig')
        assert source.count('defeat_claimed = claim_pve_terminal(user_id, "defeat")') == 3
        assert source.count('if not defeat_claimed:') == 3
        print('PVE_DEFEAT_TERMINAL_CLAIM_18_XX_1_OK')
    finally:
        pve.conn, pve.cursor = old_conn, old_cursor
        conn.close()
