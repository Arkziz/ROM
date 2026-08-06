from __future__ import annotations

import ast
import hashlib
import json
import py_compile
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CLASSES = ("warrior", "knight", "scout", "rogue", "mage", "priest")
EXPECTED_SKILLS_PER_CLASS = 3
PVP_MULTIPLIERS = {
    "damage": 1.00,
    "healing": 1.00,
    "shield": 1.00,
    "debuff": 1.00,
}

APPROVED_RULES = {
    "same_skill_definitions_as_pve": True,
    "separate_pvp_skill_overrides": False,
    "simultaneous_rounds": True,
    "action_timeout_seconds": 20,
    "timeout_action": "afk_skip",
    "automatic_basic_attack_on_timeout": False,
    "consecutive_afk_limit": 5,
    "both_afk_limit_same_round": "technical_draw",
    "maximum_rounds": 50,
    "round_limit_tiebreak": "higher_hp_percent_then_draw",
    "potions_allowed": False,
    "production_hp_mp_changed": False,
    "production_durability_changed": False,
    "production_exploration_energy_changed": False,
    "rewards_exp_gold_loot_guild": False,
    "duel_local_hp_start_percent": 100,
    "duel_local_mp_start_percent": 100,
    "duel_local_rage_start": 0,
    "duel_local_combat_energy_start": 100,
    "duel_local_combo_start": 0,
    "duel_local_cooldowns_start": 0,
    "duel_local_effects_start_empty": True,
    "stun_applies_next_round": True,
    "stun_counts_as_afk": False,
    "cleanse_removes_existing_debuffs_only": True,
    "cleanse_removes_stun": False,
    "dot_ticks_can_crit": False,
    "dot_hot_refresh": "replace_power_and_duration",
    "simultaneous_lethal_result": "draw",
    "pvp_damage_multiplier": 1.00,
    "pvp_healing_multiplier": 1.00,
    "pvp_shield_multiplier": 1.00,
    "pvp_debuff_multiplier": 1.00,
    "pvp_deferred_balance_overrides": True,
}


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_state(path: Path) -> dict[str, Any]:
    return {"exists": path.exists(), "size": path.stat().st_size if path.exists() else None, "sha256": sha256(path)}


def find_assignment(tree: ast.AST, name: str) -> list[ast.AST]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                found.append(node)
    return found


def literal_assignment(tree: ast.AST, name: str) -> Any:
    nodes = find_assignment(tree, name)
    if len(nodes) != 1:
        raise ValueError(f"{name}: expected exactly one assignment, found {len(nodes)}")
    node = nodes[0]
    value = node.value
    return ast.literal_eval(value)


def function_index(tree: ast.Module) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            index.setdefault(node.name, []).append({"line": node.lineno, "end_line": getattr(node, "end_lineno", node.lineno), "kind": type(node).__name__})
    return index


def normalize_skill(skill: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "key", "name", "cost_type", "cost", "min_cost", "cooldown",
        "damage_multiplier", "attack_type", "effect", "duration",
        "stun_chance", "combo_gain", "consume_all", "spend_all",
        "resource_gain", "scaling", "scale_by_rage", "scale_by_combo",
        "scale_by_pdef",
    )
    return {key: skill.get(key) for key in keys if key in skill}


def inspect_skill_catalog(findings: list[dict[str, str]]) -> dict[str, Any]:
    candidates = [ROOT / "handlers/combat.py", ROOT / "handlers/combat_handler.py"]
    source_path = next((path for path in candidates if path.exists()), None)
    if source_path is None:
        findings.append({"severity": "BLOCKER", "code": "combat_handler_missing", "message": "Не знайдено handlers/combat.py або handlers/combat_handler.py"})
        return {"source": None, "classes": {}, "total_skills": 0}
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    try:
        catalog = literal_assignment(tree, "CLASS_SKILLS_V1")
    except Exception as error:
        findings.append({"severity": "BLOCKER", "code": "skill_catalog_unreadable", "message": str(error)})
        return {"source": str(source_path.relative_to(ROOT)), "classes": {}, "total_skills": 0}
    if not isinstance(catalog, dict):
        findings.append({"severity": "BLOCKER", "code": "skill_catalog_type", "message": "CLASS_SKILLS_V1 має бути словником"})
        return {"source": str(source_path.relative_to(ROOT)), "classes": {}, "total_skills": 0}
    classes: dict[str, Any] = {}
    total = 0
    for class_key in EXPECTED_CLASSES:
        skills = catalog.get(class_key)
        if not isinstance(skills, (list, tuple)):
            findings.append({"severity": "BLOCKER", "code": "class_skills_missing", "message": f"{class_key}: відсутній список навичок"})
            skills = []
        if len(skills) != EXPECTED_SKILLS_PER_CLASS:
            findings.append({"severity": "BLOCKER", "code": "skill_count", "message": f"{class_key}: expected 3 skills, found {len(skills)}"})
        normalized = []
        keys_seen = set()
        for skill in skills:
            if not isinstance(skill, dict):
                findings.append({"severity": "BLOCKER", "code": "skill_type", "message": f"{class_key}: skill definition is not a dict"})
                continue
            missing = [key for key in ("key", "cost_type", "cooldown") if key not in skill]
            if missing:
                findings.append({"severity": "BLOCKER", "code": "skill_fields", "message": f"{class_key}/{skill.get('key', '?')}: missing {missing}"})
            skill_key = str(skill.get("key", ""))
            if skill_key in keys_seen:
                findings.append({"severity": "BLOCKER", "code": "duplicate_skill_key", "message": f"{class_key}: duplicate key {skill_key}"})
            keys_seen.add(skill_key)
            normalized.append(normalize_skill(skill))
        classes[class_key] = normalized
        total += len(normalized)
    extras = sorted(set(catalog) - set(EXPECTED_CLASSES))
    if extras:
        findings.append({"severity": "REVIEW", "code": "extra_skill_classes", "message": f"Unexpected classes in CLASS_SKILLS_V1: {extras}"})
    return {
        "source": str(source_path.relative_to(ROOT)),
        "source_sha256": sha256(source_path),
        "classes": classes,
        "total_skills": total,
        "expected_total": len(EXPECTED_CLASSES) * EXPECTED_SKILLS_PER_CLASS,
    }


def inspect_architecture() -> dict[str, Any]:
    files = []
    tokens = {token: [] for token in ("duel", "duel_request", "pvp_battle", "interaction_type", "activity_type", "process_new_updates")}
    roots = [ROOT / "systems", ROOT / "handlers", ROOT / "data"]
    for base in roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            try:
                text = path.read_text(encoding="utf-8")
                tree = ast.parse(text, filename=str(path))
            except Exception:
                continue
            relative = str(path.relative_to(ROOT)).replace("\\", "/")
            files.append({"path": relative, "sha256": sha256(path), "definitions": function_index(tree)})
            lowered = text.lower()
            for token in tokens:
                if token in lowered:
                    tokens[token].append(relative)
    return {"tokens": tokens, "files_scanned": len(files), "files": files}


def inspect_database(findings: list[dict[str, str]]) -> dict[str, Any]:
    path = ROOT / "game.db"
    if not path.exists():
        return {"exists": False, "quick_check": "not_available", "foreign_key_issues": None, "pvp_tables": []}
    uri = f"file:{path.as_posix()}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        connection.execute("PRAGMA query_only=ON")
        quick = connection.execute("PRAGMA quick_check").fetchone()[0]
        fk = connection.execute("PRAGMA foreign_key_check").fetchall()
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        connection.close()
    except Exception as error:
        findings.append({"severity": "BLOCKER", "code": "database_read", "message": str(error)})
        return {"exists": True, "quick_check": "error", "foreign_key_issues": None, "pvp_tables": []}
    if quick != "ok":
        findings.append({"severity": "BLOCKER", "code": "database_integrity", "message": f"PRAGMA quick_check={quick}"})
    if fk:
        findings.append({"severity": "BLOCKER", "code": "database_fk", "message": f"foreign_key_check issues={len(fk)}"})
    pvp_tables = [name for name in tables if "pvp" in name.lower() or "duel" in name.lower()]
    return {"exists": True, "quick_check": quick, "foreign_key_issues": len(fk), "pvp_tables": pvp_tables, "table_count": len(tables)}


def inspect_existing_pvp_modules() -> list[str]:
    found = []
    for base in (ROOT / "systems", ROOT / "handlers", ROOT / "data"):
        if base.exists():
            for path in base.rglob("*.py"):
                if "pvp" in path.name.lower() or "duel" in path.name.lower():
                    found.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return sorted(found)


def write_outputs(result: dict[str, Any]) -> None:
    md = ROOT / "MD"
    tools = ROOT / "tools"
    md.mkdir(exist_ok=True)
    tools.mkdir(exist_ok=True)
    json_path = md / "PVP_ARCHITECTURE_SKILL_PARITY_AUDIT_14_0_0.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit_lines = [
        "# PvP Architecture, Skill Parity and Specification Audit 14.0.0",
        "",
        f"- Verdict: **{result['verdict']}**",
        f"- Findings: **{len(result['findings'])}**",
        f"- Skill catalog: `{result['skill_catalog']['source']}`",
        f"- Classes: **{len(result['skill_catalog']['classes'])}/6**",
        f"- Skills: **{result['skill_catalog']['total_skills']}/18**",
        "- Gameplay mutations: **0**",
        "- Database writes: **0**",
        "",
        "## Multipliers fixed for PvP V1",
        "",
        "```python",
        "PVP_DAMAGE_MULTIPLIER = 1.00",
        "PVP_HEALING_MULTIPLIER = 1.00",
        "PVP_SHIELD_MULTIPLIER = 1.00",
        "PVP_DEBUFF_MULTIPLIER = 1.00",
        "```",
        "",
        "## Skill policy",
        "",
        "PvP V1 reuses the current PvE skill definitions one-to-one. No separate PvP costs, cooldowns, multipliers or duplicate skill catalog are introduced in Stage 14.0.0.",
        "",
        "## Findings",
    ]
    if result["findings"]:
        for item in result["findings"]:
            audit_lines.append(f"- [{item['severity']}] `{item['code']}`: {item['message']}")
    else:
        audit_lines.append("- None.")
    audit_lines.extend(["", "## Architecture tokens", ""])
    for token, paths in result["architecture"]["tokens"].items():
        audit_lines.append(f"- `{token}`: {len(paths)} file(s)")
    (md / "PVP_ARCHITECTURE_SKILL_PARITY_AUDIT_14_0_0.md").write_text("\n".join(audit_lines) + "\n", encoding="utf-8")

    spec = """# PvP V1 Canonical Specification 14.0.0

## Canonical principle

PvP uses the current PvE class skill catalog one-to-one. PvP V1 does not create separate skill costs, cooldowns, damage multipliers, effect durations or duplicate skill definitions.

## Central PvP modifiers

```python
PVP_DAMAGE_MULTIPLIER = 1.00
PVP_HEALING_MULTIPLIER = 1.00
PVP_SHIELD_MULTIPLIER = 1.00
PVP_DEBUFF_MULTIPLIER = 1.00
```

The values are configuration points. They remain `1.00` until PvP simulation data justify a deliberate balance change.

## Entry and request

- A duel can be proposed only to an online player in the same location.
- Self-duel is forbidden.
- Both players must be outside PvE combat and not busy in trade, duel or another blocking activity.
- The existing interaction request and activity-session architecture should be reused.

## Isolated duel state

- Production HP, MP, exploration energy, durability, active PvE effects and cooldowns are not mutated by the duel.
- Duel-local HP starts at 100%.
- Duel-local MP starts at 100% for mana classes.
- Rage starts at 0.
- Combat Energy starts at 100.
- Combo starts at 0.
- Cooldowns start at 0.
- Active effects start empty.
- On completion, cancellation, timeout or restart recovery, production state remains unchanged.

## Round contract

- Both participants choose independently.
- Action timeout is 20 seconds.
- Timeout produces `afk_skip`, never an automatic basic attack.
- Stun produces `stunned_skip` and does not increment AFK.
- Five consecutive AFK skips cause defeat.
- If both reach the AFK limit in the same round, the result is a technical draw.
- Maximum duration is 50 rounds.
- At round limit, higher HP percentage wins; equal HP percentage is a draw.

## Resolution phases

1. Start-of-round DoT and HoT.
2. Duration and cooldown updates.
3. Terminal check after periodic effects.
4. Stun state.
5. Action collection.
6. Revision, actor, resource, combo and cooldown validation.
7. Defensive preparation, including shield, self-buff and cleanse.
8. Offensive calculations from a round-start snapshot.
9. Atomic application of both results.
10. Terminal result and next-round creation.

## Effects

- A stun applied in round N affects round N+1 and does not cancel an already chosen action in round N.
- Cleanse removes only debuffs that existed before simultaneous action resolution; it does not remove stun.
- A debuff applied simultaneously in the same round remains.
- DoT ticks do not roll critical hits.
- Reapplying the same DoT or HoT replaces power and duration; it does not stack or extend them.
- Simultaneous lethal results produce a draw.

## Items, rewards and penalties

- HP and MP potions are unavailable.
- No EXP, gold, loot, guild progress or achievements are awarded in V1.
- No item loss, gold loss, durability loss or death penalty occurs.
- Exploration energy is not consumed.

## Persistence and safety

- PvP battle state must be persisted in SQLite, not only in Python memory.
- Every callback carries battle ID, round number, revision and actor ownership.
- Stale callbacks do not mutate state.
- Round resolution is atomically claimed by one worker.
- Restart recovery restores timers or resolves expired rounds as AFK according to persisted deadlines.
"""
    (md / "PVP_V1_CANONICAL_SPECIFICATION_14_0_0.md").write_text(spec, encoding="utf-8")

    roadmap = """# PvP Stage 14 Implementation Roadmap

## 14.0.0 Architecture, skill parity and specification audit

Read-only audit, canonical PvP V1 specification and skill parity snapshot.

## 14.1.0 PvP data model, sessions and recovery

Persistent battles, participants, round actions, events, interaction-session conversion, deadlines and restart recovery. No playable combat UI yet.

## 14.2.0 Simultaneous PvP round engine

Pure and deterministic intent resolver with snapshot calculations, atomic application, resources, cooldowns, shield, stun, DoT, HoT, cleanse, AFK and draw rules.

## 14.3.0 Duel request and player-interaction UI

Map action, propose duel, accept, decline, expiration, same-location and busy checks.

## 14.4.0 Round UI, actions and timer

Battle messages, action buttons, skill availability, 20-second deadlines, stale callback guards and synchronized status rendering.

## 14.5.0 Completion, cleanup and restart recovery

Victory, defeat, draw, AFK, cancellation, maximum-round handling, production-state preservation, keyboard restoration and orphan cleanup.

## 14.6.0 PvP balance simulator and class matrix

Six-by-six class matrix, levels 1/5/10, equipment profiles, seeded trials, win/draw rates, rounds, burst, control, shield, DoT and HoT contribution. Central PvP modifiers remain configurable.

## 14.7.0 Final audit and full documentation

Regression suite, DB integrity, restart tests, abuse tests, manual scenarios and full Stage 14 documentation.
"""
    (md / "PVP_IMPLEMENTATION_ROADMAP_14_0_0.md").write_text(roadmap, encoding="utf-8")

    manifest_lines = [
        "version=14.0.0",
        f"verdict={result['verdict']}",
        f"findings={len(result['findings'])}",
        f"skill_source={result['skill_catalog']['source']}",
        f"skill_source_sha256={result['skill_catalog'].get('source_sha256')}",
        f"classes={len(result['skill_catalog']['classes'])}",
        f"skills={result['skill_catalog']['total_skills']}",
        "pvp_damage_multiplier=1.00",
        "pvp_healing_multiplier=1.00",
        "pvp_shield_multiplier=1.00",
        "pvp_debuff_multiplier=1.00",
        "separate_pvp_skill_overrides=false",
        "gameplay_mutations=0",
        "database_writes=0",
        "next_stage=patch_14_1_0_pvp_data_model_sessions_and_recovery.py",
    ]
    for path in (
        md / "PVP_ARCHITECTURE_SKILL_PARITY_AUDIT_14_0_0.md",
        json_path,
        md / "PVP_V1_CANONICAL_SPECIFICATION_14_0_0.md",
        md / "PVP_IMPLEMENTATION_ROADMAP_14_0_0.md",
    ):
        manifest_lines.append(f"file={path.relative_to(ROOT)}|sha256={sha256(path)}|size={path.stat().st_size}")
    (tools / "pvp_stage_14_manifest.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")


def main() -> None:
    findings: list[dict[str, str]] = []
    before = {name: file_state(ROOT / name) for name in ("game.db", "game.db-wal")}
    skill_catalog = inspect_skill_catalog(findings)
    architecture = inspect_architecture()
    database = inspect_database(findings)
    existing_pvp_modules = inspect_existing_pvp_modules()

    if skill_catalog.get("total_skills") != 18:
        findings.append({"severity": "BLOCKER", "code": "skill_total", "message": f"Expected 18 skills, found {skill_catalog.get('total_skills')}"})
    if not architecture["tokens"].get("duel"):
        findings.append({"severity": "REVIEW", "code": "duel_architecture_token", "message": "У Python-коді не знайдено токен duel; Stage 14.1 має додати або уточнити інтеграційний шлях"})
    if database.get("pvp_tables"):
        findings.append({"severity": "INFO", "code": "existing_pvp_tables", "message": f"Existing PvP/duel tables: {database['pvp_tables']}"})
    else:
        findings.append({"severity": "INFO", "code": "pvp_tables_pending", "message": "Persistent PvP tables ще не створені; очікувано до Stage 14.1.0"})

    blocker_count = sum(item["severity"] == "BLOCKER" for item in findings)
    review_count = sum(item["severity"] == "REVIEW" for item in findings)
    verdict = "FAIL" if blocker_count else ("REVIEW" if review_count else "PASS")
    result = {
        "schema": "rom.pvp.architecture.skill_parity.audit.v1",
        "version": "14.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "findings": findings,
        "skill_catalog": skill_catalog,
        "approved_rules": APPROVED_RULES,
        "pvp_multipliers": PVP_MULTIPLIERS,
        "architecture": architecture,
        "database": database,
        "existing_pvp_modules": existing_pvp_modules,
        "gameplay_mutations": 0,
        "database_writes": 0,
    }
    write_outputs(result)
    after = {name: file_state(ROOT / name) for name in ("game.db", "game.db-wal")}
    if before != after:
        raise RuntimeError("game.db or game.db-wal changed during read-only PvP audit")

    print("[OK] PvP architecture, skill parity and specification audit")
    print(f"- verdict: {verdict}")
    print(f"- findings: {len(findings)}")
    print(f"- classes: {len(skill_catalog.get('classes', {}))}/6")
    print(f"- skills: {skill_catalog.get('total_skills', 0)}/18")
    print("- PvE skill catalog reused one-to-one: YES")
    print("- separate PvP skill overrides: NO")
    print("- PvP multipliers damage/healing/shield/debuff: 1.00/1.00/1.00/1.00")
    print("- gameplay mutations: 0")
    print("- database writes: 0")
    print("- game.db/WAL unchanged: YES")
    for item in findings:
        print(f"  [{item['severity']}] {item['code']}: {item['message']}")
    if verdict == "FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
