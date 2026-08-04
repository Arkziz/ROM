from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

VERSION = "13.0.0"
TARGET_MODULES = (
    "systems/combat_system.py",
    "systems/player_system.py",
    "systems/equipment_system.py",
    "systems/rune_system.py",
    "systems/refine_system.py",
    "systems/reward_system.py",
    "systems/contract_system.py",
    "systems/guild_system.py",
    "systems/energy_system.py",
    "systems/regen_system.py",
    "systems/character_system.py",
    "systems/drop_system.py",
    "systems/potion_system.py",
    "handlers/dev.py",
    "db.py",
    "main.py",
)

OUTPUTS = (
    "MD/SIMULATION_ARCHITECTURE_AUDIT.md",
    "MD/SIMULATION_MVP_POLICY_SPECIFICATION.md",
    "MD/SIMULATION_IMPLEMENTATION_ROADMAP.md",
    "SIMULATION_CALLABILITY_MATRIX.json",
    "tools/simulation_stage_13_manifest.txt",
)

MUTATION_METHODS = {
    "execute", "executemany", "executescript", "commit", "rollback",
    "add_gold", "add_exp", "add_kill", "add_item", "consume_inventory_item",
    "set_current_hp", "set_user_mp", "set_inventory_refine_level",
    "equip_inventory_item", "unequip_inventory_item", "repair_equipped_item",
    "repair_all_equipped", "sell_inventory_item_to_trader", "create_daily_contract",
    "claim_contract_reward", "insert_rune_into_equipment", "fuse_runes_with_firius_token",
    "perform_refine_attempt", "award_guild_elite_kill", "award_guild_contract_completion",
}
READ_METHODS = {
    "fetchone", "fetchall", "get_player_stats", "get_player_level", "get_wallet",
    "get_max_hp", "get_current_hp", "get_physical_defense", "get_magic_defense",
    "get_all_equipped_items", "get_inventory_detailed", "get_character_class",
    "get_user_energy", "get_active_contract", "get_contract_status",
}
RNG_NAMES = {"random", "randint", "randrange", "choice", "choices", "uniform", "shuffle", "sample"}
TIME_NAMES = {"datetime", "date", "time", "today", "now", "utcnow", "monotonic", "sleep"}
TELEGRAM_NAMES = {"send_message", "edit_message_text", "answer_callback_query", "reply_to", "message_handler", "callback_query_handler"}
FILESYSTEM_NAMES = {"open", "write_text", "write_bytes", "read_text", "read_bytes", "unlink", "replace", "mkdir"}
SQL_WRITE_PREFIXES = ("insert", "update", "delete", "create", "alter", "drop", "replace", "vacuum", "pragma wal_checkpoint")
SQL_READ_PREFIXES = ("select", "with", "pragma table_info", "pragma index_list", "pragma foreign_key_list")


def root_dir() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parent.parent, Path.cwd().resolve()):
        if (candidate / "systems").is_dir() and (candidate / "db.py").exists():
            return candidate
    raise RuntimeError("Запускай аудит з кореня ROM або з ROM\\patch")


def sha(path: Path):
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return {"size": path.stat().st_size, "sha256": h.hexdigest()}


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = dotted(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return ""


def literal_string(node):
    try:
        value = ast.literal_eval(node)
        return value if isinstance(value, str) else ""
    except Exception:
        return ""


def sql_kind(text):
    normalized = " ".join(str(text or "").lower().split())
    if normalized.startswith(SQL_WRITE_PREFIXES):
        return "write"
    if normalized.startswith(SQL_READ_PREFIXES):
        return "read"
    return "unknown"


def line_range(node):
    return [int(getattr(node, "lineno", 0)), int(getattr(node, "end_lineno", getattr(node, "lineno", 0)))]


def classify_function(module, node, module_imports):
    calls = []
    imports = set(module_imports)
    sql_reads = []
    sql_writes = []
    dynamic_sql = False
    flags = set()
    reasons = []

    for sub in ast.walk(node):
        if isinstance(sub, (ast.Import, ast.ImportFrom)):
            if isinstance(sub, ast.Import):
                imports.update(alias.name for alias in sub.names)
            else:
                imports.add(sub.module or "")
        elif isinstance(sub, ast.Call):
            name = dotted(sub.func)
            leaf = name.rsplit(".", 1)[-1]
            calls.append(name)
            if leaf in RNG_NAMES or name.startswith("random."):
                flags.add("GLOBAL_RNG_DEPENDENT")
            if leaf in TIME_NAMES or name.startswith(("datetime.", "date.", "time.")):
                flags.add("TIME_DEPENDENT")
            if leaf in TELEGRAM_NAMES or name.startswith(("bot.", "telebot.")):
                flags.add("TELEGRAM_DEPENDENT")
            if leaf in FILESYSTEM_NAMES and (name.startswith(("Path.", "pathlib.")) or leaf == "open"):
                flags.add("FILESYSTEM_DEPENDENT")
            if leaf in MUTATION_METHODS:
                flags.add("MUTATING_STATE")
            if leaf in READ_METHODS:
                flags.add("READS_STATE")
            if leaf in {"execute", "executemany", "executescript"}:
                text = literal_string(sub.args[0]) if sub.args else ""
                kind = sql_kind(text)
                if kind == "write":
                    flags.add("MUTATING_DB")
                    sql_writes.append(text[:240])
                elif kind == "read":
                    flags.add("READ_ONLY_DB")
                    sql_reads.append(text[:240])
                else:
                    dynamic_sql = True
                    flags.add("DB_DYNAMIC_SQL")
            if name.startswith(("db.", "sqlite3.")) or leaf in {"cursor", "connect"}:
                flags.add("DB_DEPENDENT")
        elif isinstance(sub, ast.Global):
            flags.add("GLOBAL_STATE_DEPENDENT")
        elif isinstance(sub, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = sub.targets if isinstance(sub, ast.Assign) else [sub.target]
            for target in targets:
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                    if target.value.id.isupper() or target.value.id.endswith("STATE"):
                        flags.add("GLOBAL_STATE_MUTATION")

    if any(x == "telebot" or x.startswith("telebot.") for x in imports):
        flags.add("TELEGRAM_MODULE")
    if module == "db.py":
        flags.add("LEGACY_FACADE_OR_MONOLITH")
    if "MUTATING_DB" in flags or ("DB_DEPENDENT" in flags and "MUTATING_STATE" in flags):
        flags.add("ADAPTER_REQUIRED")
    if "TELEGRAM_DEPENDENT" in flags or "TELEGRAM_MODULE" in flags:
        flags.add("ADAPTER_REQUIRED")
    if "GLOBAL_RNG_DEPENDENT" in flags:
        flags.add("RNG_INJECTION_REQUIRED")
    if "TIME_DEPENDENT" in flags:
        flags.add("CLOCK_INJECTION_REQUIRED")

    pure_blockers = flags & {
        "MUTATING_DB", "READ_ONLY_DB", "DB_DEPENDENT", "DB_DYNAMIC_SQL",
        "TELEGRAM_DEPENDENT", "TELEGRAM_MODULE", "FILESYSTEM_DEPENDENT",
        "GLOBAL_STATE_DEPENDENT", "GLOBAL_STATE_MUTATION", "GLOBAL_RNG_DEPENDENT", "TIME_DEPENDENT",
    }
    if not pure_blockers:
        flags.add("PURE_CANDIDATE")
        safe = True
        action = "Використовувати напряму після parity-тесту."
    elif pure_blockers <= {"GLOBAL_RNG_DEPENDENT"}:
        safe = True
        action = "Додати ін'єкцію seeded RNG; формулу не дублювати."
    elif pure_blockers <= {"TIME_DEPENDENT"}:
        safe = True
        action = "Додати SimulationClock."
    elif "MUTATING_DB" in flags or "TELEGRAM_DEPENDENT" in flags or "GLOBAL_STATE_MUTATION" in flags:
        safe = False
        action = "Не викликати на real DB; потрібен simulation adapter або pure rule extraction."
    elif "READ_ONLY_DB" in flags or "DB_DEPENDENT" in flags:
        safe = False
        action = "Винести обчислення в pure rule, дані передавати через SimulationState."
    else:
        safe = False
        action = "Потрібен ручний review перед підключенням."

    if module.startswith("handlers/") or module == "main.py":
        safe = False
        flags.add("PRESENTATION_OR_ENTRYPOINT")
        action = "Не використовувати в engine; лише окремий DEV handler для запуску та звітів."

    return {
        "module": module,
        "function": node.name,
        "async": isinstance(node, ast.AsyncFunctionDef),
        "line_range": line_range(node),
        "args": [a.arg for a in node.args.args],
        "classification": sorted(flags),
        "safe_for_exact_simulation": bool(safe),
        "recommended_action": action,
        "calls": sorted(set(c for c in calls if c))[:120],
        "sql_reads": sql_reads[:20],
        "sql_writes": sql_writes[:20],
        "dynamic_sql": dynamic_sql,
    }


def analyze_module(path: Path, rel: str):
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=rel)
    imports = set()
    module_effects = []
    functions = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(classify_function(rel, node, imports))
        elif isinstance(node, (ast.Expr, ast.Assign, ast.AnnAssign, ast.AugAssign, ast.For, ast.While, ast.With, ast.Try)):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    name = dotted(sub.func)
                    if name and name not in {"globals", "getattr", "hasattr", "setattr", "len", "str", "int", "float", "list", "dict", "tuple", "set"}:
                        module_effects.append({"call": name, "line": getattr(sub, "lineno", 0)})
    return {
        "module": rel,
        "sha256": sha(path)["sha256"],
        "size": path.stat().st_size,
        "imports": sorted(imports),
        "module_scope_calls": module_effects[:100],
        "functions": functions,
    }


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def md_escape(value):
    return str(value).replace("|", "\\|")


def build_policy_md():
    return """# ROM Simulation MVP Policy Specification 13.0.0

## Статус

Це затверджена стартова policy-специфікація для PvE та progression simulator. PvP не входить у MVP і відкладається до появи production PvP ruleset.

## Безпека

- Симулятор не змінює `game.db`, реальних users, inventory, guilds або trade.
- Усі simulation runs використовують `SimulationState` у пам'яті або окремий тимчасовий fixture.
- RNG обов'язково seeded і записується у звіт.
- Production та simulation повинні використовувати спільні pure rules. Формули не копіюються в handlers.

## Inventory

- Production baseline: 40 комірок.
- Experiment: 60 комірок.
- Capacity передається через config, а не hardcode усередині engine.
- Reserve slots policy: 2.
- Один generated equipment instance займає одну комірку.
- Один stack займає одну комірку; stack merge можливий навіть при повній сумці, поки `quantity < max_stack`.
- При необхідності нового row і повній сумці drop втрачається або reward не видається відповідно до production contract.
- Метрики: full bag events, forced city returns, lost drops, lost value, average free slots, utilization.

## Профілі часу

- Casual: 18:00-21:00.
- Regular: 17:00-23:00.
- Hardcore: 09:00-23:00.
- Energy max: 40.
- Regeneration: +1 кожні 5 хвилин до максимуму.
- Усередині active window персонаж відновлює активність після regeneration tick; поза вікном лише минає час і відновлюються ресурси.

## Моби й локації

- Доступні лише unlocked locations.
- Пул мобів: рівень гравця -1, рівень гравця, рівень гравця +1.
- Active contract target має пріоритет, якщо target доступний.
- Використовувати чинний runtime selector або винесене з нього pure rule.
- Боси обробляються окремою policy, а не як випадковий normal mob.

## Зілля

- HP potion: `current_hp / max_hp < 0.30`.
- MP potion: `current_mp / max_mp < 0.25`, лише mana-класи.
- Ураховувати production cooldown.
- Обирати найменше доступне зілля, достатнє для корисного відновлення; fallback на наступне доступне.

## Ремонт

- Плановий ремонт під час city visit.
- Термінове повернення до міста, якщо будь-яка активна річ має `durability < 10`.
- Перед ремонтом продати trash і непотрібне/несумісне спорядження.
- Repair metrics: count, total cost, downtime, restored score.

## Екіпірування

1. Несумісний із класом предмет продається.
2. Порожній сумісний слот заповнюється.
3. Зайнятий слот порівнюється через class-aware effective score.
4. Рідкість не перемагає автоматично: білий предмет вищого рівня може бути кращим за синій нижчого рівня.
5. Score враховує relevant stats, damage, PDEF/MDEF, refine, durability, inserted runes і доступні socket opportunities.
6. Дворучна зброя порівнюється із сумою current main-hand + off-hand.
7. Одноручна зброя після дворучної оцінюється разом із найкращим доступним compatible off-hand.
8. Ваги класів є simulation policy і мають калібруватися через PvE результати.

## Combat action policy

MVP policy: `balanced`.

Пріоритет:
1. survival heal/shield, якщо прогнозується смерть;
2. HP potion за порогом;
3. MP potion за порогом;
4. control/defense у небезпечному бою;
5. skill, який завершує бій;
6. class finisher за оптимального ресурсу;
7. найкраща доступна offensive skill;
8. basic attack.

Майбутні policies: `safe`, `balanced`, `aggressive`.

## Acceptance baseline

`/dev_progress_sim warrior 20 regular` у режимі EXACT має завершити progression 1-20, створити JSON/Markdown звіт і не змінити real DB. Звіт охоплює бої, час, енергію, EXP, gold, deaths, loot, repair, contracts, daily, runes, fusion, refine, guild contribution, final equipment і final stats.
"""


def build_architecture_md(result):
    s = result["summary"]
    module_rows = []
    for mod in result["modules"]:
        counts = Counter()
        for f in mod["functions"]:
            counts.update(f["classification"])
        module_rows.append(
            f"| `{mod['module']}` | {len(mod['functions'])} | {counts['PURE_CANDIDATE']} | "
            f"{counts['READ_ONLY_DB']} | {counts['MUTATING_DB']} | {counts['GLOBAL_RNG_DEPENDENT']} | "
            f"{counts['TIME_DEPENDENT']} | {counts['TELEGRAM_DEPENDENT'] + counts['TELEGRAM_MODULE']} |"
        )
    top_adapters = [f for m in result["modules"] for f in m["functions"] if "ADAPTER_REQUIRED" in f["classification"]]
    top_rng = [f for m in result["modules"] for f in m["functions"] if "RNG_INJECTION_REQUIRED" in f["classification"]]
    top_time = [f for m in result["modules"] for f in m["functions"] if "CLOCK_INJECTION_REQUIRED" in f["classification"]]
    module_scope = [x for m in result["modules"] for x in ({"module": m["module"], **e} for e in m["module_scope_calls"])]
    lines = [
        "# Simulation Architecture & Purity Audit 13.0.0", "",
        f"Generated: `{result['generated_at']}`", "",
        f"Verdict: **{result['verdict']}**", "",
        "## Executive summary", "",
        f"- Target modules found: **{s['modules_found']} / {s['modules_expected']}**.",
        f"- Functions analyzed: **{s['functions']}**.",
        f"- Pure candidates: **{s['pure_candidates']}**.",
        f"- Safe for direct EXACT use after parity tests: **{s['safe_exact']}**.",
        f"- Adapter required: **{s['adapter_required']}**.",
        f"- RNG injection required: **{s['rng_injection_required']}**.",
        f"- Clock injection required: **{s['clock_injection_required']}**.",
        f"- Missing modules: **{len(result['missing_modules'])}**.", "",
        "## Classification", "",
        "| Module | Functions | Pure | Read DB | Write DB | RNG | Time | Telegram |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        *module_rows, "",
        "## Architecture findings", "",
        "1. Production domain is not uniformly pure. A substantial part of behavior is tied to SQLite, global RNG, wall-clock time, or legacy facade calls.",
        "2. The simulation engine must own state, clock, RNG and metrics. It must not create real users in `game.db`.",
        "3. Mathematical rules and selectors should be extracted or wrapped as pure functions and used by both production and simulation.",
        "4. DEV Telegram handlers must only validate commands, enqueue/run simulations and return compact summaries plus report files.",
        "5. PvP is explicitly deferred until production PvP rules exist.", "",
        "## Highest-priority adapters", "",
    ]
    for f in top_adapters[:80]:
        lines.append(f"- `{f['module']}::{f['function']}()` lines {f['line_range'][0]}-{f['line_range'][1]}: {f['recommended_action']}")
    lines += ["", "## Seeded RNG candidates", ""]
    for f in top_rng[:60]:
        lines.append(f"- `{f['module']}::{f['function']}()`")
    lines += ["", "## SimulationClock candidates", ""]
    for f in top_time[:60]:
        lines.append(f"- `{f['module']}::{f['function']}()`")
    lines += ["", "## Module-scope calls requiring caution", ""]
    if module_scope:
        for e in module_scope[:100]:
            lines.append(f"- `{e['module']}` line {e['line']}: `{e['call']}()`")
    else:
        lines.append("- No significant module-scope calls detected by the static heuristic.")
    lines += ["", "## Inventory capacity", "",
        "- Current production baseline discovered/expected: 40 slots.",
        "- Experimental scenario: 60 slots.",
        "- Simulator config must support arbitrary capacity and reserve slots.",
        "- Capacity analysis must distinguish stack merge from creating a new inventory row.", "",
        "## Limitations of this audit", "",
        "- Static AST classification is conservative and may mark facade functions as adapter-required even when a lower-level pure helper exists.",
        "- Dynamic imports, aliases and SQL assembled at runtime require manual review.",
        "- A function marked PURE_CANDIDATE still requires parity tests against production behavior before use.",
    ]
    return "\n".join(lines) + "\n"


def roadmap(result):
    s = result["summary"]
    complexity = "high" if s["adapter_required"] > max(25, s["functions"] * 0.20) else "medium"
    estimated = 9 if complexity == "high" else 7
    return f"""# Simulation implementation roadmap after audit 13.0.0

## Preliminary estimate

Static result indicates **{complexity} integration complexity**. Preliminary implementation estimate: **{estimated} core stages**, excluding PvP and optional optimization stages. This is an audit-based estimate and should be finalized after reviewing the generated callability matrix.

## Proposed stages

1. **13.1 Simulation foundation**: dataclasses/models, SimulationState, SimulationClock, seeded RNG, config, metrics, report serialization.
2. **13.2 Canonical pure rules and parity layer**: extract/wrap damage, crit, dodge, reward, repair, refine, compatibility and capacity rules; parity tests against production.
3. **13.3 Exact single-battle PvE engine**: normal/elite/boss, skills, cooldowns, class resources, potions, durability, deterministic seeds.
4. **13.4 Drop and inventory simulation**: central drop system, stack plans, 40/60 capacity, lost loot, city return, sell rules.
5. **13.5 Behavior policy engine**: equipment score, 1H/2H comparison, potion/repair/mob/skill policies, rune insertion/fusion/refine.
6. **13.6 Progression MVP**: level path and progress simulation, active windows, energy, regen, contracts, daily, guild contribution.
7. **13.7 Analytics and comparison**: PvE class balance, progression walls, loot acquisition, rune completion, 40-vs-60 capacity.
8. **13.8 Economy and population**: inflation, guild cohorts, lifecycle checkpoints, FAST-mode calibration against EXACT.
9. **13.9 RNG and patch regression**: baseline/current snapshots, same-seed comparison, lucky/average/unlucky percentiles.

## Deferred

- `systems/pvp_simulator.py`, `/dev_pvp`, `/dev_pvp_all` until production PvP exists.
- Player-facing trade history and PvP implementation are outside this analytics stage.

## Quality gates for every stage

- Real `game.db` SHA-256 unchanged.
- No real user, inventory or guild mutations.
- Seed and config fingerprint recorded.
- Own smoke test plus core regression suite.
- Exact behavior parity tests where a production rule is reused.
- Manual game check only for Telegram DEV handler/UX stages.
"""


def main():
    root = root_dir()
    before = {name: sha(root / name) for name in ("game.db", "game.db-wal")}
    modules = []
    missing = []
    syntax_errors = []
    for rel in TARGET_MODULES:
        path = root / rel
        if not path.exists():
            missing.append(rel)
            continue
        try:
            modules.append(analyze_module(path, rel))
        except SyntaxError as error:
            syntax_errors.append({"module": rel, "error": str(error)})

    all_functions = [f for m in modules for f in m["functions"]]
    counts = Counter()
    for f in all_functions:
        counts.update(f["classification"])
    summary = {
        "modules_expected": len(TARGET_MODULES),
        "modules_found": len(modules),
        "functions": len(all_functions),
        "pure_candidates": counts["PURE_CANDIDATE"],
        "safe_exact": sum(1 for f in all_functions if f["safe_for_exact_simulation"]),
        "adapter_required": counts["ADAPTER_REQUIRED"],
        "rng_injection_required": counts["RNG_INJECTION_REQUIRED"],
        "clock_injection_required": counts["CLOCK_INJECTION_REQUIRED"],
        "read_only_db": counts["READ_ONLY_DB"],
        "mutating_db": counts["MUTATING_DB"],
        "telegram_dependent": counts["TELEGRAM_DEPENDENT"] + counts["TELEGRAM_MODULE"],
    }
    blockers = []
    critical = {"systems/combat_system.py", "systems/player_system.py", "systems/reward_system.py", "systems/equipment_system.py"}
    for rel in missing:
        if rel in critical:
            blockers.append({"code": "missing_critical_module", "message": rel})
    for item in syntax_errors:
        blockers.append({"code": "syntax_error", "message": f"{item['module']}: {item['error']}"})
    if not all_functions:
        blockers.append({"code": "no_functions", "message": "No functions analyzed"})

    result = {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": "FAIL" if blockers else "PASS",
        "blockers": blockers,
        "missing_modules": missing,
        "syntax_errors": syntax_errors,
        "summary": summary,
        "policies": {
            "pvp_deferred": True,
            "inventory_capacity_baseline": 40,
            "inventory_capacity_experiment": 60,
            "inventory_reserve_slots": 2,
            "hp_potion_threshold": 0.30,
            "mp_potion_threshold": 0.25,
            "repair_threshold_strictly_below": 10,
            "mob_level_delta": [-1, 0, 1],
            "energy_max": 40,
            "energy_regen_minutes": 5,
            "profiles": {"casual": "18:00-21:00", "regular": "17:00-23:00", "hardcore": "09:00-23:00"},
        },
        "modules": modules,
        "database_files_before": before,
    }

    write_json(root / "SIMULATION_CALLABILITY_MATRIX.json", result)
    (root / "MD").mkdir(parents=True, exist_ok=True)
    (root / "MD/SIMULATION_ARCHITECTURE_AUDIT.md").write_text(build_architecture_md(result), encoding="utf-8")
    (root / "MD/SIMULATION_MVP_POLICY_SPECIFICATION.md").write_text(build_policy_md(), encoding="utf-8")
    (root / "MD/SIMULATION_IMPLEMENTATION_ROADMAP.md").write_text(roadmap(result), encoding="utf-8")

    after = {name: sha(root / name) for name in ("game.db", "game.db-wal")}
    strict_unchanged = before == after
    result["database_files_after"] = after
    result["database_files_unchanged"] = strict_unchanged
    if not strict_unchanged:
        result["verdict"] = "FAIL"
        result["blockers"].append({"code": "database_changed", "message": "game.db or WAL changed during AST-only audit"})
    write_json(root / "SIMULATION_CALLABILITY_MATRIX.json", result)

    output_paths = [root / x for x in OUTPUTS[:-1]]
    manifest_lines = [
        f"version={VERSION}",
        f"generated_at={result['generated_at']}",
        f"verdict={result['verdict']}",
        f"functions_analyzed={summary['functions']}",
        f"pure_candidates={summary['pure_candidates']}",
        f"adapter_required={summary['adapter_required']}",
        f"rng_injection_required={summary['rng_injection_required']}",
        f"clock_injection_required={summary['clock_injection_required']}",
        f"database_files_unchanged={str(strict_unchanged).lower()}",
        "pvp_deferred=true",
        "inventory_capacity_baseline=40",
        "inventory_capacity_experiment=60",
    ]
    for path in output_paths:
        info = sha(path)
        manifest_lines.append(f"file={path.relative_to(root)}|size={info['size']}|sha256={info['sha256']}")
    manifest_path = root / OUTPUTS[-1]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    print("[OK] ROM simulation architecture and purity audit")
    print(f"- verdict: {result['verdict']}")
    print(f"- modules: {summary['modules_found']}/{summary['modules_expected']}")
    print(f"- functions analyzed: {summary['functions']}")
    print(f"- pure candidates: {summary['pure_candidates']}")
    print(f"- adapter required: {summary['adapter_required']}")
    print(f"- seeded RNG injection required: {summary['rng_injection_required']}")
    print(f"- SimulationClock injection required: {summary['clock_injection_required']}")
    print(f"- game.db/WAL unchanged: {'YES' if strict_unchanged else 'NO'}")
    print("- PvP: DEFERRED")
    print("- inventory scenarios: 40 baseline / 60 experiment")
    print("- report: MD\\SIMULATION_ARCHITECTURE_AUDIT.md")
    print("- policy: MD\\SIMULATION_MVP_POLICY_SPECIFICATION.md")
    print("- roadmap: MD\\SIMULATION_IMPLEMENTATION_ROADMAP.md")
    print("- matrix: SIMULATION_CALLABILITY_MATRIX.json")
    if result["blockers"]:
        for finding in result["blockers"]:
            print(f"  [BLOCKER] {finding['code']}: {finding['message']}")
    if result["verdict"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
