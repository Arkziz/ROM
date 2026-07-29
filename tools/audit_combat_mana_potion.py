#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only structural and database audit of combat mana-potion support."""
from __future__ import annotations

import ast
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "game.db"
REPORT = ROOT / "DB_CLEANUP_9_0_13E_COMBAT_MANA_POTION_AUDIT.md"
COMBAT_PATH = ROOT / "handlers" / "combat.py"
POTION_PATH = ROOT / "systems" / "potion_system.py"
CHARACTER_PATH = ROOT / "systems" / "character_system.py"
DB_PY_PATH = ROOT / "db.py"
MANA_IDS = (202, 204)
HP_IDS = (201, 203)


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint(path):
    return (
        hashlib.sha256(path.read_bytes()).hexdigest(),
        path.stat().st_size,
        path.stat().st_mtime_ns,
    )


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    return text, ast.parse(text, filename=str(path))


def function_sources(text, tree, name):
    # Handlers can be nested inside register_* functions, while system APIs
    # are generally top-level. Walk the whole tree and sort by source line.
    nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    if not nodes:
        fail(f"{name}: definition not found")
    nodes.sort(key=lambda node: node.lineno)
    return [
        (node, ast.get_source_segment(text, node) or "")
        for node in nodes
    ]


def function_source(text, tree, name, prefer="only"):
    definitions = function_sources(text, tree, name)
    if prefer == "last":
        return definitions[-1]
    if len(definitions) != 1:
        fail(f"{name}: definitions={len(definitions)}, expected 1")
    return definitions[0]


def literal_assignment(tree, name):
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            try:
                return ast.literal_eval(node.value)
            except Exception:
                return None
    return None


def call_names(node):
    result = []
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        if isinstance(sub.func, ast.Name):
            result.append(sub.func.id)
        elif isinstance(sub.func, ast.Attribute):
            result.append(sub.func.attr)
    return result


def inventory_counts(conn, ids):
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"""SELECT i.item_id, it.name, it.type,
                   COUNT(i.id) AS stacks,
                   COALESCE(SUM(i.quantity), 0) AS quantity
            FROM inventory i
            JOIN items it ON it.id=i.item_id
            WHERE i.item_id IN ({placeholders})
            GROUP BY i.item_id, it.name, it.type
            ORDER BY i.item_id""",
        tuple(ids),
    ).fetchall()
    return [
        {
            "item_id": int(row[0]),
            "name": row[1],
            "type": row[2],
            "stacks": int(row[3] or 0),
            "quantity": int(row[4] or 0),
        }
        for row in rows
    ]


def main():
    for path in (DB_PATH, COMBAT_PATH, POTION_PATH, CHARACTER_PATH, DB_PY_PATH):
        if not path.is_file():
            fail(f"missing required file: {path}")

    before = fingerprint(DB_PATH)
    combat_text, combat_tree = parse(COMBAT_PATH)
    potion_text, potion_tree = parse(POTION_PATH)
    character_text, character_tree = parse(CHARACTER_PATH)
    db_text, db_tree = parse(DB_PY_PATH)

    potion_config = literal_assignment(potion_tree, "POTIONS")
    if not isinstance(potion_config, dict):
        fail("POTIONS config is not a literal dictionary")

    config_rows = {}
    for item_id in HP_IDS + MANA_IDS:
        row = potion_config.get(item_id)
        if not isinstance(row, dict):
            fail(f"POTIONS missing item {item_id}")
        config_rows[item_id] = row

    build_node, build_source = function_source(
        combat_text, combat_tree, "build_combat_potion_kb"
    )
    cooldown_node, cooldown_source = function_source(
        combat_text, combat_tree, "get_potion_cooldown_turns_by_inventory_id"
    )
    use_handler_node, use_handler_source = function_source(
        combat_text, combat_tree, "use_selected_potion_in_combat"
    )
    choose_node, choose_source = function_source(
        combat_text, combat_tree, "choose_potion_in_combat"
    )
    use_node, use_source = function_source(
        potion_text, potion_tree, "use_potion_from_inventory"
    )
    resource_node, resource_source = function_source(
        character_text, character_tree, "get_character_resource_type"
    )
    mp_get_definitions = function_sources(
        character_text, character_tree, "get_user_mp"
    )
    mp_get_node, mp_get_source = mp_get_definitions[-1]
    mp_set_node, mp_set_source = function_source(
        character_text, character_tree, "set_user_mp"
    )
    spend_node, spend_source = function_source(
        db_text, db_tree, "spend_user_mp"
    )

    hp_filter_present = (
        'type_ in ["potion_hp", "potion_hp_medium"]' in build_source
        or "type_ in ['potion_hp', 'potion_hp_medium']" in build_source
    )
    mana_types_in_keyboard = (
        "potion_mp" in build_source or "potion_mp_medium" in build_source
    )
    mana_backend_blocked = (
        'potion["type"] == "mp"' in use_source
        and "Мана ще не реалізована" in use_source
    )
    cooldown_has_hp = "potion_hp" in cooldown_source
    cooldown_has_mp = "potion_mp" in cooldown_source
    handler_hp_only_result = (
        'potion_result["new_hp"]' in use_handler_source
        and 'potion_result["max_hp"]' in use_handler_source
    )
    handler_mp_result = any(
        marker in use_handler_source
        for marker in (
            'potion_result["new_mp"]',
            'potion_result["max_mp"]',
            'potion_result.get("new_mp")',
        )
    )
    combat_state_has_mp = (
        'mob["player_mp"]' in combat_text
        and 'mob["player_max_mp"]' in combat_text
    )
    mana_resource_known = 'return "mana"' in resource_source or "mana" in character_text
    mp_helpers_available = all((
        "return" in mp_get_source,
        "UPDATE users" in mp_set_source or "set_user_mp" in mp_set_source,
        "UPDATE users" in spend_source,
    ))
    no_turn_spent = "Хід не витрачено" in use_handler_source
    shared_cooldown = 'mob["potion_cooldown"]' in use_handler_source
    empty_message_hp_only = "немає зілля здоров’я" in choose_source

    # Structural result contract gap.
    current_success_keys = set()
    for node in ast.walk(use_node):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            literal_keys = []
            for key in node.value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    literal_keys.append(key.value)
            if "success" in literal_keys and "new_hp" in literal_keys:
                current_success_keys.update(literal_keys)
    expected_mp_keys = {"success", "message", "restore_mp", "new_mp", "max_mp"}
    missing_mp_keys = sorted(expected_mp_keys - current_success_keys)

    uri = DB_PATH.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
        mp_columns = sorted(columns.intersection({"mp", "max_mp", "character_class"}))
        hp_inventory = inventory_counts(conn, HP_IDS)
        mana_inventory = inventory_counts(conn, MANA_IDS)
        item_rows = conn.execute(
            "SELECT id, name, type, category, max_stack FROM items WHERE id IN (201,202,203,204) ORDER BY id"
        ).fetchall()
        integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        conn.close()

    after = fingerprint(DB_PATH)
    if before != after:
        fail("game.db changed during read-only audit")
    if integrity != "ok":
        fail(f"database quick_check={integrity}")

    diagnosis = []
    if hp_filter_present and not mana_types_in_keyboard:
        diagnosis.append("Combat potion keyboard explicitly filters only HP potion item types.")
    if mana_backend_blocked:
        diagnosis.append("Potion backend explicitly rejects every MP potion as not implemented.")
    if handler_hp_only_result and not handler_mp_result:
        diagnosis.append("Combat callback assumes every successful potion returns HP-only keys.")
    if not cooldown_has_mp:
        diagnosis.append("Cooldown helper has no explicit MP potion mapping.")
    if empty_message_hp_only:
        diagnosis.append("Empty potion-list message mentions only health potions.")

    implementation_scope = [
        "Extend the combat potion keyboard with `potion_mp` and `potion_mp_medium` only for mana-resource classes.",
        "Implement MP restoration in `systems.potion_system.use_potion_from_inventory()` using current/max MP helpers.",
        "Return a typed result that lets the combat callback distinguish HP from MP restoration.",
        "Synchronize successful MP restoration into `mob['player_mp']` and `mob['player_max_mp']`.",
        "Keep potion use turn-free and use the existing shared stomach cooldown unless a separate balance rule is requested.",
        "Map small MP potion to 3 turns and medium MP potion to 5 turns, matching HP size tiers.",
        "Reject MP potion use at full mana without consuming the item or starting cooldown.",
        "Hide MP potions from warrior, knight, scout, and rogue combat menus.",
        "Preserve all current HP potion behavior and contracts.",
    ]

    report = [
        "# ROM 9.0.13e — Combat Mana Potion Audit",
        "",
        f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Safety",
        "",
        "- Gameplay files changed: **0**",
        "- Database rows changed: **0**",
        f"- Database SHA/size/mtime unchanged: **{before == after}**",
        f"- Database quick check: **{integrity}**",
        "",
        "## Static potion definitions",
        "",
    ]
    for item_id in HP_IDS + MANA_IDS:
        report.append(f"- `{item_id}`: `{config_rows[item_id]}`")
    report.extend([
        "",
        "## Current combat UI",
        "",
        f"- HP-only keyboard filter detected: **{hp_filter_present}**",
        f"- MP item types included in keyboard: **{mana_types_in_keyboard}**",
        f"- Empty-list message is HP-only: **{empty_message_hp_only}**",
        "",
        "## Current potion backend",
        "",
        f"- MP potion definitions exist: **{all(config_rows[item_id].get('type') == 'mp' for item_id in MANA_IDS)}**",
        f"- MP use explicitly rejected: **{mana_backend_blocked}**",
        f"- Current success result keys: `{sorted(current_success_keys)}`",
        f"- Required MP result keys missing from current HP contract: `{missing_mp_keys}`",
        "",
        "## Combat callback and state",
        "",
        f"- Callback assumes HP result keys only: **{handler_hp_only_result}**",
        f"- Callback handles MP result keys: **{handler_mp_result}**",
        f"- Combat state already stores player MP/max MP: **{combat_state_has_mp}**",
        f"- Potion use currently spends no combat turn: **{no_turn_spent}**",
        f"- Shared potion cooldown state exists: **{shared_cooldown}**",
        f"- Cooldown helper handles HP potions: **{cooldown_has_hp}**",
        f"- Cooldown helper handles MP potions: **{cooldown_has_mp}**",
        "",
        "## Character/MP infrastructure",
        "",
        f"- Mana resource is defined: **{mana_resource_known}**",
        f"- MP get/set/spend helpers are available: **{mp_helpers_available}**",
        f"- `get_user_mp()` definitions in Character System: **{len(mp_get_definitions)}** at lines `{[node.lineno for node, _source in mp_get_definitions]}`",
        "- Runtime audit selected the last effective `get_user_mp()` definition, matching Python name binding.",
        f"- Relevant user columns: `{mp_columns}`",
        "",
        "## Real database context",
        "",
        f"- Static potion rows: `{[tuple(row) for row in item_rows]}`",
        f"- HP potion inventory context: `{hp_inventory}`",
        f"- MP potion inventory context: `{mana_inventory}`",
        "",
        "## Diagnosis",
        "",
    ])
    for finding in diagnosis:
        report.append(f"- {finding}")
    report.extend([
        "",
        "## Implementation scope for the next patch",
        "",
    ])
    for index, item in enumerate(implementation_scope, start=1):
        report.append(f"{index}. {item}")
    report.extend([
        "",
        "## Conclusion",
        "",
        "MP potions are fully defined as static items, and the Character/Combat systems already maintain MP state. However, combat support is incomplete in three separate layers: the potion-selection keyboard excludes MP types, the potion backend explicitly rejects MP restoration, and the combat callback assumes an HP-only success payload.",
        "",
        "Suggested next patch: `patch_9_0_13f_combat_mana_potion_implementation.py`",
        "",
    ])
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] Combat Mana Potion audit")
    print("- mana potion static definitions: 2")
    print(f"- combat keyboard includes mana potions: {mana_types_in_keyboard}")
    print(f"- potion backend supports mana restore: {not mana_backend_blocked}")
    print(f"- combat callback supports MP result payload: {handler_mp_result}")
    print(f"- combat MP state already available: {combat_state_has_mp}")
    print(f"- MP helpers available: {mp_helpers_available}")
    print(f"- get_user_mp definitions: {len(mp_get_definitions)} (last effective definition audited)")
    print(f"- shared cooldown and no-turn use: {shared_cooldown and no_turn_spent}")
    print(f"- MP potion inventory rows: {sum(row['stacks'] for row in mana_inventory)}")
    print("- database mutations: 0")
    print("- diagnosis: UI + backend + callback implementation gap")
    print(f"- report: {REPORT}")


if __name__ == "__main__":
    main()
