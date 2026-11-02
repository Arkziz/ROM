# Stage 21.3.1 — SQLite connection policy runtime audit

- Status: **PASS_READ_ONLY**
- Parent: `4b41a0796322630fdbd36d3d084ad2a658da547f`
- Python files parsed: `957`
- Direct `sqlite3.connect` calls: `211`
- Production runtime direct connections: `21`
- Tool/test direct connections: `190`
- Production SQLite opened: **NO**
- Production DB/WAL/SHM mutations: **NONE**
- Manual game check: **NOT REQUIRED**

## Findings

- **production_direct_connections / REVIEW_REQUIRED**: production runtime sqlite3.connect calls=21
- **tool_test_connections / INVENTORIED**: tool/test sqlite3.connect calls=190
- **connection_factory_candidates / INVENTORIED**: factory-like definitions=24
- **pragma_policy / REVIEW_REQUIRED**: source PRAGMA calls=264; snapshot pragmas={'journal_mode': 'wal', 'foreign_keys': 0, 'busy_timeout': 30000, 'query_only': 0, 'user_version': 0, 'schema_version': 158, 'synchronous': 2}
- **transaction_ownership / REVIEW_REQUIRED**: commit/rollback/transaction-related calls=716
- **database_integrity / PASS**: quick_check=['ok']; foreign_key_rows=0

## Decision

`GO_TO_21_3_2_SQLITE_CONNECTION_POLICY_IMPLEMENTATION`

Implementation must classify production owners separately from tools/tests, preserve special consumers, centralize only proven common policy, and never manipulate production WAL/SHM.
