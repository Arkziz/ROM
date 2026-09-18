# -*- coding: utf-8 -*-
"""Immutable receipt log for idempotent event shop operations."""
def up(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS event_shop_transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      idempotency_key TEXT NOT NULL UNIQUE,
      event_key TEXT NOT NULL,user_id INTEGER NOT NULL,offer_key TEXT NOT NULL,
      operation_kind TEXT NOT NULL,reward_kind TEXT NOT NULL,
      cost_item_id INTEGER NOT NULL,cost_quantity INTEGER NOT NULL,
      reward_item_id INTEGER NOT NULL,reward_quantity INTEGER NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
      FOREIGN KEY(cost_item_id) REFERENCES items(id) ON DELETE RESTRICT,
      FOREIGN KEY(reward_item_id) REFERENCES items(id) ON DELETE RESTRICT
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_event_shop_user ON event_shop_transactions(user_id,event_key,created_at DESC,id DESC)")
