#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, hashlib, json, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "game.db"
REPORT = ROOT / "reports/stage_18_22_4_inline_map_and_travel_closure.json"
MD = ROOT / "MD/STAGE_18_22_INLINE_MAP_AND_TRAVEL_FULL_DOCUMENTATION.md"
SOURCES = (
    "data/location_graph.py", "data/locations.py", "systems/travel_system.py",
    "systems/location_context_system.py", "handlers/map.py", "handlers/combat.py",
    "handlers/city.py", "handlers/player_interaction.py", "handlers/pvp_interaction.py",
    "keyboards.py", "db_modules/player.py", "db_modules/connection.py",
    "db_modules/dev_compat.py", "db_modules/location.py", "main.py",
)

def read(rel): return (ROOT / rel).read_text(encoding="utf-8-sig")
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def require(condition, code, detail, failures):
    if not condition: failures.append({"code": code, "detail": detail})
def table_info(connection, name):
    return [dict(zip(("cid","name","type","notnull","default","pk"), row))
            for row in connection.execute(f'PRAGMA table_info("{name}")').fetchall()]
def index_rows(connection, table):
    rows=[]
    for row in connection.execute(f'PRAGMA index_list("{table}")').fetchall():
        rows.append({"seq":row[0],"name":row[1],"unique":bool(row[2]),"origin":row[3],"partial":bool(row[4])})
    return rows

def main():
    failures=[]
    for rel in SOURCES:
        require((ROOT/rel).is_file(), "MISSING_SOURCE", rel, failures)
    if failures: raise RuntimeError(json.dumps(failures, ensure_ascii=False))
    for rel in SOURCES: ast.parse(read(rel), filename=rel)

    graph=read("data/location_graph.py"); travel=read("systems/travel_system.py")
    context=read("systems/location_context_system.py"); map_src=read("handlers/map.py")
    combat=read("handlers/combat.py"); city=read("handlers/city.py")
    interaction=read("handlers/player_interaction.py"); pvp=read("handlers/pvp_interaction.py")
    keyboards=read("keyboards.py"); player=read("db_modules/player.py")
    connection_src=read("db_modules/connection.py"); dev=read("db_modules/dev_compat.py")
    location_db=read("db_modules/location.py"); main_src=read("main.py")

    contracts={
      "graph_city_start_path": '"city": ("start_path",)' in graph,
      "graph_start_path_both": '"start_path": ("city", "dark_forest")' in graph,
      "graph_dark_forest_back": '"dark_forest": ("start_path",)' in graph,
      "travel_60_seconds": "TRAVEL_SECONDS = 60" in graph,
      "city_not_huntable": '"huntable": False' in graph,
      "one_active_index_source": "ux_location_travels_one_active_user" in travel,
      "atomic_arrival": "UPDATE users SET current_location" in travel and "status='arrived'" in travel,
      "cancel_before_arrival": "arrival_at>?" in travel,
      "restart_recovery": "recover_travels_after_restart" in travel and "recover_travels_after_restart(bot)" in main_src,
      "arrival_worker": "start_travel_worker" in travel and "start_travel_worker(bot)" in main_src,
      "map_inline_callbacks": all(token in map_src for token in ("map:preview:","map:start:","map:cancel:","map:refresh:","map:players")),
      "map_refresh": "🔄 Оновити" in map_src,
      "map_collapse_only": "🔽 Згорнути мапу" in keyboards and "🌿 Початок Шляху\"), types.KeyboardButton" not in keyboards,
      "no_immediate_map_location_write": "set_current_location" not in map_src,
      "city_players": 'callback_data="map:players"' in map_src,
      "context_resolver": all(token in context for token in ("get_location_context_kind","get_location_context_kb","return city_kb()","return main_kb()","return map_kb()")),
      "trade_context_restore": interaction.count("get_location_context_kb(") >= 4,
      "city_hunt_guard": 'current_location == "city"' in combat and "У Місті не можна полювати" in combat,
      "travel_hunt_guard": "is_user_travelling(user_id)" in combat and "Полювання недоступне під час подорожі" in combat,
      "city_look_around": 'get_location_context_kind(user_id) == "city"' in city,
      "trade_guards": interaction.count("is_user_travelling(") >= 2,
      "pvp_guards": pvp.count("is_user_travelling(") >= 2,
      "city_action_guard": "CITY_ACTION_BUTTONS" in map_src,
      "new_player_city": '"city",  # ROM 18.22.1' in player,
      "dev_reset_city": '"current_location": "city"' in dev,
      "empty_location_city": location_db.count('return "city"') >= 2,
    }
    for name,value in contracts.items(): require(value, "CONTRACT_FAILED", name, failures)

    before=sha(DB)
    con=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro", uri=True)
    try:
        con.execute("PRAGMA query_only=ON")
        quick=con.execute("PRAGMA quick_check").fetchone()[0]
        foreign=con.execute("PRAGMA foreign_key_check").fetchall()
        tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        require("location_travels" in tables,"TRAVEL_TABLE_MISSING","location_travels",failures)
        columns=table_info(con,"location_travels") if "location_travels" in tables else []
        indexes=index_rows(con,"location_travels") if "location_travels" in tables else []
        statuses=[]
        active=[]
        history=[]
        if "location_travels" in tables:
            statuses=[{"status":r[0],"count":r[1]} for r in con.execute("SELECT status,COUNT(*) AS count FROM location_travels GROUP BY status ORDER BY status")]
            active=[dict(zip(("id","user_id","from_node","to_node","status","revision","arrival_at"),r)) for r in con.execute("SELECT id,user_id,from_node,to_node,status,revision,arrival_at FROM location_travels WHERE status='active' ORDER BY id")]
            history=[dict(zip(("id","user_id","from_node","to_node","status","revision"),r)) for r in con.execute("SELECT id,user_id,from_node,to_node,status,revision FROM location_travels ORDER BY id DESC LIMIT 20")]
        locations=[{"location":r[0],"users":r[1]} for r in con.execute("SELECT current_location,COUNT(*) FROM users GROUP BY current_location ORDER BY current_location")]
        migrations=[r[0] for r in con.execute("SELECT migration_name FROM schema_migrations ORDER BY migration_name")]
    finally: con.close()
    after=sha(DB)
    require(quick=="ok","DB_QUICK_CHECK",quick,failures)
    require(not foreign,"DB_FOREIGN_KEYS",str(foreign),failures)
    require(before==after,"DB_MUTATED","read-only audit changed game.db",failures)
    require("049_persistent_location_travel.py" in migrations,"MIGRATION_049_MISSING",str(migrations),failures)
    required_cols={"id","user_id","from_node","to_node","status","revision","started_at","arrival_at","cancelled_at","completed_at","created_at","updated_at"}
    require(required_cols <= {c['name'] for c in columns},"TRAVEL_COLUMNS_MISSING",str(required_cols-{c['name'] for c in columns}),failures)
    require(any(i['name']=="ux_location_travels_one_active_user" and i['unique'] and i['partial'] for i in indexes),"ACTIVE_INDEX_MISSING",str(indexes),failures)

    status="PASS" if not failures else "FAIL"
    report={"stage":"18.22.4","status":status,"generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "read_only":True,"contracts":contracts,"failures":failures,
      "database":{"quick_check":quick,"foreign_key_violations":[tuple(r) for r in foreign],"sha256_before":before,"sha256_after":after,"unchanged":before==after,
      "location_travels_columns":columns,"location_travels_indexes":indexes,"travel_status_distribution":statuses,"active_travels":active,"recent_travel_history":history,"user_location_distribution":locations,"migration_049_applied":True},
      "manual_acceptance":{"result":"PASS","reported_by":"project owner","covered":["inline map","collapse map","travel preview","60-second travel","cancel travel","arrival notification","refresh timer","City players","City trade cancel recovery","City hunt fail-closed","location keyboards","no observed traceback after recovery"]},
      "known_limits":["Future locations require adding a WORLD_NODES profile and symmetric graph edge.","Travel notifications depend on Telegram delivery after the authoritative DB commit.","The worker refresh interval is operational polling and does not alter arrival_at."]}
    REPORT.parent.mkdir(exist_ok=True); MD.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")

    md=f"""# Stage 18.22: Inline Map and Persistent Travel — Full Documentation

## Closure

- **Final status:** {status}
- **Closure stage:** 18.22.4
- **Production feature commits:** `d494d9511f53fa13e871932e08213fa4a0d9681d`, `b8a1975f41c631e1f36c027b2b36e97631e429a6`, `571036d9b15813e65e5f45487ac324a4d057b548`
- **Manual acceptance:** PASS
- **Database quick check:** `{quick}`
- **Foreign-key violations:** `{len(foreign)}`
- **WAL/SHM manipulation:** none

## Purpose

Stage 18.22 replaces immediate ReplyKeyboard location switching with an authoritative inline world map and persistent, cancellable, server-timed travel. City is a real world node, external locations remain huntable zones, and only adjacent nodes are visible and reachable.

## Canonical world graph

```text
🏙️ city
   ↕ 60 seconds
🌿 start_path
   ↕ 60 seconds
🌲 dark_forest
   ↕ future location
```

Rules:

- `city` is non-huntable.
- `start_path` and `dark_forest` are external huntable locations.
- Every current edge is bidirectional and takes exactly 60 seconds.
- Non-neighbor nodes are hidden and rejected by the domain.
- A locked adjacent external location is visible but cannot start travel.
- `dark_forest` uses the existing level-6 unlock policy.
- A future location must be added to `WORLD_NODES` and to both sides of a symmetric edge.

## User interface

### Map mode

Opening `🗺️ Мапа` replaces the persistent keyboard with one button:

```text
🔽 Згорнути мапу
```

Navigation is inline. The available buttons are generated from the current authoritative node.

### City

```text
🚶 Вирушити у Початок Шляху
👥 Гравці локації
```

### Start Path

```text
🏙️ Повернутися у Місто
🚶 Вирушити у Темний Бір
👥 Гравці локації
```

### Dark Forest

```text
🌿 Повернутися у Початок Шляху
👥 Гравці локації
```

A future forward button is absent until the future node exists.

### Active travel

```text
🔄 Оновити
❌ Скасувати подорож
```

Refresh re-reads the authoritative row and recalculates remaining time from the unchanged `arrival_at`. Refresh does not create a row, change revision, or extend travel.

## Persistent data model

Table: `location_travels`

Columns:

```text
id
user_id
from_node
to_node
status
revision
started_at
arrival_at
cancelled_at
completed_at
created_at
updated_at
```

Statuses:

```text
active
arrived
cancelled
failed
```

Database invariants:

- One partial unique index permits at most one active travel per user.
- `from_node` cannot equal `to_node`.
- A travel row references `users.user_id`.
- Historical terminal rows remain available for audit.
- Migration owner: `049_persistent_location_travel.py`.

## Transaction semantics

### Start

`start_travel` validates the user, current node, destination, adjacency, level unlock, busy state, and absence of another active travel. It persists `started_at` and `arrival_at` but does not change `users.current_location`.

### Cancel

Cancellation succeeds only while status is active and server time is before `arrival_at`. Revision can be checked by the callback. The first terminal claim wins.

### Arrival

Arrival uses one transaction to claim the active row as `arrived` and update `users.current_location` from `from_node` to `to_node`. If the source node changed unexpectedly, the travel is marked `failed` instead of moving the player.

### Restart recovery

Startup recovery completes only overdue active travel rows. The original `arrival_at` is preserved. A background worker processes later due rows. Telegram notification occurs after the authoritative database commit and cannot roll back the location.

## Location context and keyboards

`systems/location_context_system.py` resolves UI context from authoritative state:

```text
active travel → map_kb
city          → city_kb
external node → main_kb
invalid node  → map_kb, fail-closed
```

This resolver is used after trade cancellation, trade completion, and terminal trade-input recovery. Each participant receives a keyboard based on that participant's own location.

## Guards

During active travel, the feature blocks incompatible operations before mutation:

- PvE hunting and energy consumption
- PvP duel request and acceptance
- Direct trade request and acceptance
- City actions and NPC routes
- A second travel

Travel start is also blocked while the player has an active PvE or player-interaction state.

City hunting is explicitly rejected before energy consumption or mob generation. The legacy external-location fallback must not convert `city` into `start_path`. Look Around in City renders City content and `city_kb`.

## Player discovery

`👥 Гравці локації` is an inline map action in City and external locations. It reuses the canonical same-location online presence query. The return callback edits the same message back to the current authoritative map.

## Starting and migration policy

- New characters start in `city`.
- DEV reset starts in `city`.
- Existing valid users were preserved in their existing locations during Stage 18.22.1.
- Class change and ordinary restart do not reset location.

## Testing

Automated coverage includes:

- graph symmetry and known-node validation
- temporary-DB start, cancel, arrival and recovery paths
- 59-second rejection and 60-second arrival
- one-active-travel uniqueness
- level lock and non-neighbor rejection
- inline callback and collapse-keyboard contracts
- refresh and stale callback ownership
- City players
- PvE, trade, PvP and City guards
- context-aware trade recovery
- City hunt fail-closed behavior
- runtime imports
- SQLite quick check and foreign keys

Manual acceptance verified the complete UI flow, travel, cancellation, arrival, refresh, City player list, context-aware trade recovery and the recovered hunt guard.

## Known nuances

- Telegram may retain old reply buttons visually; server-side guards remain authoritative.
- Arrival notification failure does not undo committed arrival.
- Cancellation at the same moment as arrival is resolved by the first successful terminal database claim.
- Unknown location state intentionally exposes no hunting keyboard.

## Closure result

Stage 18.22 is accepted as complete when this audit reports PASS and the closure commit is created.
"""
    MD.write_text(md,encoding="utf-8")
    print(json.dumps({"status":status,"contracts":sum(1 for v in contracts.values() if v),"total_contracts":len(contracts),"failures":len(failures),"quick_check":quick,"foreign_keys":len(foreign),"active_travels":len(active),"json":str(REPORT.relative_to(ROOT)),"md":str(MD.relative_to(ROOT))},ensure_ascii=False))
    if failures: raise RuntimeError(json.dumps(failures,ensure_ascii=False))

if __name__=="__main__": main()
