#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, hashlib, json, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "game.db"
REPORT = ROOT / "reports/stage_18_22_0_inline_map_and_travel_read_only_audit.json"
MD = ROOT / "MD/STAGE_18_22_0_INLINE_MAP_AND_TRAVEL_READ_ONLY_AUDIT.md"
FILES = (
    "data/locations.py", "db_modules/location.py", "db_modules/connection.py",
    "handlers/map.py", "handlers/city.py", "handlers/player_interaction.py",
    "handlers/combat.py", "keyboards.py", "systems/player_interaction_system.py",
    "systems/pve_auto_escape_system.py", "systems/pvp_system.py", "main.py",
)

TARGET = {
    "travel_seconds": 60,
    "start_node": "city",
    "external_chain": ["start_path", "dark_forest"],
    "edges": [["city", "start_path"], ["start_path", "dark_forest"]],
    "map_reply_keyboard": ["🔽 Згорнути мапу"],
    "city_inline": ["🚶 Вирушити у Початок Шляху"],
    "start_path_inline": ["🏙️ Повернутися у Місто", "🌲 Вирушити у Темний Бір", "👥 Гравці локації"],
    "dark_forest_inline": ["🌿 Повернутися у Початок Шляху", "👥 Гравці локації"],
    "non_neighbor_policy": "hidden",
    "locked_neighbor_policy": "visible_locked_by_existing_level_rule",
    "arrival_notification": True,
    "cancellable": True,
    "persistent_restart_recovery": True,
    "travel_blocks": ["PvE", "PvP", "trade", "duel", "new travel", "city actions"],
}

def read(rel): return (ROOT/rel).read_text(encoding="utf-8-sig")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def function_rows(rel):
    src=read(rel); tree=ast.parse(src,filename=rel); rows=[]
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            seg=ast.get_source_segment(src,n) or ""
            rows.append({"name":n.name,"line":n.lineno,"end":getattr(n,"end_lineno",n.lineno),"source":seg})
    return rows
def handlers(rel):
    src=read(rel); tree=ast.parse(src,filename=rel); out=[]
    for n in ast.walk(tree):
        if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
        seg=ast.get_source_segment(src,n) or ""
        if "@bot.message_handler" in seg or "@bot.callback_query_handler" in seg:
            out.append({"name":n.name,"line":n.lineno,"message_handler":"@bot.message_handler" in seg,"callback_handler":"@bot.callback_query_handler" in seg,"source":seg})
    return out
def table_info(con,name):
    return [dict(zip(("cid","name","type","notnull","default","pk"),row)) for row in con.execute(f'PRAGMA table_info("{name}")').fetchall()]
def literal_locations():
    ns={}; exec(compile(read("data/locations.py"),"data/locations.py","exec"),ns)
    locs=ns["LOCATIONS"]; order=ns["LOCATION_ORDER"]
    return {"order":list(order),"locations":{k:{"id":v.get("id"),"name":v.get("name"),"unlock_level":v.get("unlock_level"),"level_min":v.get("level_min"),"level_max":v.get("level_max"),"description":v.get("description")} for k,v in locs.items()}}
def text_hits(rel,needles):
    lines=read(rel).splitlines(); out=[]
    for i,line in enumerate(lines,1):
        found=[x for x in needles if x in line]
        if found: out.append({"line":i,"matches":found,"text":line.strip()[:500]})
    return out

def main():
    for rel in FILES:
        if not (ROOT/rel).is_file(): raise RuntimeError("missing audit source: "+rel)
        ast.parse(read(rel),filename=rel)
    before=sha(DB)
    con=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True); con.row_factory=sqlite3.Row
    try:
        con.execute("PRAGMA query_only=ON")
        quick=con.execute("PRAGMA quick_check").fetchone()[0]
        fk=con.execute("PRAGMA foreign_key_check").fetchall()
        tables=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        users_cols=table_info(con,"users")
        travel_tables=[t for t in tables if "travel" in t.lower() or "journey" in t.lower()]
        travel_schema={t:table_info(con,t) for t in travel_tables}
        current_rows=con.execute("SELECT current_location,COUNT(*) AS n FROM users GROUP BY current_location ORDER BY current_location").fetchall()
        location_distribution=[{"current_location":r[0],"users":r[1]} for r in current_rows]
        total_changes=con.total_changes
    finally: con.close()
    after=sha(DB)

    locations=literal_locations()
    map_handlers=handlers("handlers/map.py")
    city_handlers=handlers("handlers/city.py")
    interaction_handlers=handlers("handlers/player_interaction.py")
    map_src=read("handlers/map.py"); kb_src=read("keyboards.py"); loc_db_src=read("db_modules/location.py")
    exact={
        "current_reply_map_has_start_path": "🌿 Початок Шляху" in kb_src,
        "current_reply_map_has_dark_forest": "🌲 Темний Бір" in kb_src,
        "current_reply_map_has_players": "👥 Гравці локації" in kb_src,
        "current_reply_map_has_city": "🏙️ Місто" in kb_src,
        "current_reply_map_has_back": "🔙 Назад" in kb_src,
        "map_has_inline_keyboard": "InlineKeyboardMarkup" in map_src,
        "map_changes_location_immediately": "set_current_location(user_id, location_id)" in map_src,
        "map_has_travel_seconds": "60" in map_src and ("travel" in map_src.lower() or "подорож" in map_src.lower()),
        "map_has_cancel_travel": "cancel" in map_src.lower() or "скасувати подорож" in map_src.lower(),
        "map_has_persistent_travel": bool(travel_tables),
        "location_writer_is_immediate_commit": "conn.commit()" in loc_db_src,
        "start_default_is_start_path": "TEXT DEFAULT 'start_path'" in read("db_modules/connection.py"),
        "dev_reset_is_start_path": '"current_location": "start_path"' in read("db_modules/dev_compat.py") if (ROOT/"db_modules/dev_compat.py").exists() else None,
    }

    callback_literals=[]
    for rel in ("handlers/map.py","handlers/player_interaction.py","handlers/city.py"):
        src=read(rel); tree=ast.parse(src,filename=rel)
        for n in ast.walk(tree):
            if isinstance(n,ast.keyword) and n.arg=="callback_data":
                try: value=ast.literal_eval(n.value)
                except Exception: value=ast.get_source_segment(src,n.value) or ""
                callback_literals.append({"file":rel,"line":getattr(n,"lineno",0),"value":value})

    busy={
        "pve_owner_candidates": [r for r in function_rows("handlers/combat.py") if r["name"] in ("is_player_in_active_combat","hunt","attack")],
        "interaction_busy_functions": [r for r in function_rows("systems/player_interaction_system.py") if r["name"] in ("is_player_interaction_busy","get_player_activity_session","acquire_player_activity_session","get_active_player_trade")],
        "pvp_signals": text_hits("systems/pvp_system.py",("active","status","battle","busy","session"))[:100],
    }

    findings=[]
    def finding(sev,code,detail): findings.append({"severity":sev,"code":code,"detail":detail})
    finding("HIGH","REPLY_MAP_NAVIGATION_IS_LEGACY","Location, city and location-player actions are currently ReplyKeyboard buttons and must move to one authoritative inline map.")
    if exact["map_changes_location_immediately"]: finding("HIGH","LOCATION_SWITCH_IS_IMMEDIATE","Current map handlers call set_current_location immediately; no 60-second travel state exists in the route.")
    if not travel_tables: finding("HIGH","PERSISTENT_TRAVEL_DOMAIN_MISSING","No travel/journey table exists in production SQLite schema.")
    if "city" not in locations["locations"]: finding("HIGH","CITY_NODE_NOT_IN_LOCATION_CONFIG","City is not a canonical location node in data/locations.py and must be introduced without making it huntable.")
    if exact["start_default_is_start_path"]: finding("HIGH","START_LOCATION_DEFAULT_CONFLICT","Current users.current_location default is start_path; approved Stage 18.22 start node is city for new/reset characters.")
    finding("MEDIUM","LOCATION_GRAPH_MISSING","LOCATION_ORDER exists, but there is no explicit canonical adjacency graph for city ↔ start_path ↔ dark_forest.")
    finding("MEDIUM","CITY_CONTEXT_DEPENDS_ON_EXTERNAL_LOCATION","Current city text uses users.current_location as an external location label; Stage 18.22 must define city-node semantics and return navigation explicitly.")
    finding("MEDIUM","PLAYER_LIST_BACK_ROUTE_REUSES_MAP","Existing player-list UI already has pi:back:map and should be adapted to the new inline map rather than duplicated.")
    finding("MEDIUM","TRAVEL_BUSY_GUARDS_REQUIRE_CONSOLIDATION","PvE and player-interaction/PvP state owners are separate; travel start and incompatible actions require one fail-closed availability policy.")
    finding("INFO","LEVEL_UNLOCK_ALREADY_CANONICAL","data/locations.py already owns unlock_level and is_location_unlocked; Stage 18.22 should reuse it for locked adjacent nodes.")

    mutation_scope={
        "new_files":["data/location_graph.py","systems/travel_system.py","migrations/049_persistent_location_travel.py","tools/smoke_test_inline_map_and_travel_18_22_1.py"],
        "likely_modified":["handlers/map.py","keyboards.py","handlers/player_interaction.py","handlers/city.py","handlers/combat.py","main.py","db_modules/__init__.py","db_modules/location.py","db_modules/connection.py","db_modules/dev_compat.py"],
        "database_candidate":{
            "table":"location_travels",
            "columns":["id","user_id","from_node","to_node","status","revision","started_at","arrival_at","cancelled_at","completed_at","created_at","updated_at"],
            "active_statuses":["active"],"terminal_statuses":["arrived","cancelled","failed"],
            "constraints":["one active travel per user","from_node != to_node","server-authoritative 60 seconds","terminal claim is atomic"]},
        "worker":"A notification/recovery worker should atomically complete due arrivals, update users.current_location, commit, then send one arrival message with the correct keyboard.",
        "migration":"Existing valid start_path/dark_forest users should remain where they are. Only new characters and DEV reset defaults change to city unless a separately approved migration says otherwise.",
    }

    report={
        "stage":"18.22.0","status":"PASS","generated_at_utc":datetime.now(timezone.utc).isoformat(),"read_only":True,
        "approved_target":TARGET,"locations":locations,"database":{"quick_check":quick,"foreign_key_violations":[tuple(r) for r in fk],"db_unchanged":before==after,"sha256_before":before,"sha256_after":after,"users_columns":users_cols,"travel_tables":travel_schema,"location_distribution":location_distribution},
        "current_behavior":exact,"map_handlers":map_handlers,"city_handlers":city_handlers,"player_interaction_handlers":interaction_handlers,
        "callback_literals":callback_literals,"busy_state_owners":busy,"findings":findings,"recommended_mutation_scope":mutation_scope,
        "invariants":[
            "Only adjacent nodes are shown and accepted.","Unknown and non-neighbor destinations fail closed.","Locked adjacent external locations remain visible but cannot start travel.",
            "All edges take exactly 60 seconds in both directions.","Location changes only in the atomic arrival transaction.","Cancellation wins only before arrival terminal claim.",
            "Restart preserves arrival_at and completes overdue travel exactly once.","Arrival notification failure cannot roll back committed location.",
            "During active travel, map shows status and cancel only.","Travel cannot start during PvE, PvP, trade, duel or another travel.",
            "PvE, PvP, trade, duel and city actions cannot start during active travel.","Map mode ReplyKeyboard contains only 🔽 Згорнути мапу.",
            "Players-in-location is an inline action in external locations and is absent in city/travel state.","Stale callbacks revalidate current node, level, adjacency, status and revision.",
            "No WAL/SHM manipulation.",
        ],
    }
    if quick!="ok" or fk or total_changes or before!=after: report["status"]="FAIL"
    REPORT.parent.mkdir(exist_ok=True); MD.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    lines=[
        "# Stage 18.22.0: Inline Map and Travel Read-only Audit","",f"**Status:** {report['status']}","**Production mutation:** none","**Database mutation:** none","",
        "## Approved target","","- World chain: `city ↔ start_path ↔ dark_forest ↔ future location`.","- Only adjacent nodes are displayed.","- Every edge takes 60 seconds in both directions.","- Map mode keeps one ReplyKeyboard button: `🔽 Згорнути мапу`.","- Location navigation, City and Players in location move to inline buttons.","- City has only the adjacent Start Path travel action.","- Start Path has return to City, travel to Dark Forest and Players in location.","- Dark Forest has return to Start Path, Players in location and a future next-location button only after that location exists.","",
        "## Current state","",f"- Canonical external locations: `{', '.join(locations['order'])}`.",f"- Persistent travel tables: `{', '.join(travel_tables) if travel_tables else 'none'}`.",f"- Immediate location mutation in map handler: `{exact['map_changes_location_immediately']}`.",f"- Current DB default is start_path: `{exact['start_default_is_start_path']}`.","",
        "## Findings","",
    ]
    lines += [f"- **{x['severity']} {x['code']}**: {x['detail']}" for x in findings]
    lines += ["","## Recommended implementation split","","1. **18.22.1 Persistent travel foundation:** graph, city node, schema, atomic start/cancel/arrival, startup recovery and worker.","2. **18.22.2 Inline map UI:** inline node actions, travel preview/status, map collapse keyboard, player-list return route and city/location keyboards.","3. **18.22.3 Cross-system guards:** PvE, PvP, direct trade/duel, city actions and stale callback protection.","4. **18.22.4 Manual acceptance and closure. — only if previous patches require separate recovery/UX passes.","","## Database safety","",f"- quick_check: `{quick}`.",f"- FK violations: `{len(fk)}`.",f"- DB unchanged: `{before==after}`.","- WAL/SHM were not manipulated.",""]
    MD.write_text("\n".join(lines),encoding="utf-8")
    if report["status"]!="PASS": raise RuntimeError("read-only invariants failed")
    print(json.dumps({"status":"PASS","locations":locations["order"],"travel_tables":travel_tables,"immediate_switch":exact["map_changes_location_immediately"],"findings":len(findings),"db_unchanged":True,"json":str(REPORT.relative_to(ROOT)),"md":str(MD.relative_to(ROOT))},ensure_ascii=False))
if __name__=="__main__": main()
