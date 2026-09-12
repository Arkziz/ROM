"""Stage 18.22.1 persistent location travel foundation."""
def up(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS location_travels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        from_node TEXT NOT NULL,
        to_node TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active'
            CHECK(status IN ('active','arrived','cancelled','failed')),
        revision INTEGER NOT NULL DEFAULT 1 CHECK(revision >= 1),
        started_at TEXT NOT NULL,
        arrival_at TEXT NOT NULL,
        cancelled_at TEXT,
        completed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK(from_node <> to_node),
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    CREATE UNIQUE INDEX IF NOT EXISTS ux_location_travels_one_active_user
        ON location_travels(user_id) WHERE status='active';
    CREATE INDEX IF NOT EXISTS ix_location_travels_due
        ON location_travels(status, arrival_at, id);
    CREATE INDEX IF NOT EXISTS ix_location_travels_user_history
        ON location_travels(user_id, id DESC);
    """)
