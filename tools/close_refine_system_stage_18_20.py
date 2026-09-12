#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import hashlib
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "game.db"
REPORT = ROOT / "reports/stage_18_20_2_refine_system_production_closure.json"
MD = ROOT / "MD/STAGE_18_20_REFINE_SYSTEM_PRODUCTION_CLOSURE.md"
PRODUCTION = ("handlers/refine.py", "systems/refine_system.py")
TESTS = ("tools/smoke_test_refine_idempotency_18_20_1.py",)
REQUIRED_STAGE_MESSAGES = ("Stage 18.20.0", "Stage 18.20.1")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            "command failed: " + " ".join(command) + "\n" + result.stdout + result.stderr
        )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout[-10000:],
        "stderr": result.stderr[-10000:],
    }


def db_check():
    before = sha256(DB)
    connection = sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        result = {
            "quick_check": connection.execute("PRAGMA quick_check").fetchone()[0],
            "foreign_key_violations": connection.execute("PRAGMA foreign_key_check").fetchall(),
            "total_changes": connection.total_changes,
        }
    finally:
        connection.close()
    result["sha256_before"] = before
    result["sha256_after"] = sha256(DB)
    result["unchanged"] = result["sha256_before"] == result["sha256_after"]
    return result


def top_functions(source):
    tree = ast.parse(source)
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def commit_for_message(message):
    result = subprocess.run(
        ["git", "log", "--format=%H%x00%s", "--all", "--grep", "^" + message + "$", "-n", "1"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode or not result.stdout.strip():
        raise RuntimeError("missing Git commit with message: " + message)
    commit_hash, subject = result.stdout.strip().split("\x00", 1)
    if subject != message:
        raise RuntimeError("unexpected commit subject for " + message)
    return commit_hash


def main():
    for relative in PRODUCTION + TESTS:
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError("missing " + relative)
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=relative)

    handler_source = (ROOT / "handlers/refine.py").read_text(encoding="utf-8-sig")
    system_source = (ROOT / "systems/refine_system.py").read_text(encoding="utf-8-sig")
    handlers = top_functions(handler_source)
    systems = top_functions(system_source)

    for name in (
        "_safe_answer_refine_callback",
        "build_refine_idempotency_key",
        "build_refine_attempt_result_text",
        "register_refine_handlers",
    ):
        if name not in handlers:
            raise RuntimeError("missing handler owner: " + name)

    for name in (
        "get_refine_success_chance",
        "roll_refine_success",
        "get_refine_failure_level",
        "perform_refine_attempt",
    ):
        if name not in systems:
            raise RuntimeError("missing system owner: " + name)

    handler_contracts = (
        'return f"telegram:refine:{int(user_id)}:{callback_id}"',
        'build_refine_idempotency_key(call.from_user.id, call.id)',
        'if result.get("idempotent_replay"):',
        "Матеріали повторно не списувалися.",
        'if "query is too old" in message or "query id is invalid" in message:',
    )
    for contract in handler_contracts:
        if contract not in handler_source:
            raise RuntimeError("missing handler contract: " + contract)

    if handler_source.count("_safe_answer_refine_callback(bot, call") < 7:
        raise RuntimeError("not all refine callback routes use safe acknowledgement")

    system_contracts = (
        "BEGIN IMMEDIATE",
        "idempotency_key TEXT NOT NULL UNIQUE",
        "refine target changed concurrently",
        "conn.rollback()",
        "roll <= chance",
    )
    for contract in system_contracts:
        if contract not in system_source:
            raise RuntimeError("missing system contract: " + contract)

    if "WEAPON_REFINE_SUCCESS_CHANCES = {0: 100, 1: 100, 2: 100" not in system_source:
        raise RuntimeError("approved weapon success table changed")
    if "ARMOR_REFINE_SUCCESS_CHANCES = {0: 100, 1: 100" not in system_source:
        raise RuntimeError("approved armor success table changed")

    commands = [
        run(
            [
                sys.executable,
                "-m",
                "py_compile",
                *[str(ROOT / relative) for relative in PRODUCTION + TESTS],
            ]
        )
    ]
    for relative in TESTS:
        commands.append(run([sys.executable, str(ROOT / relative)]))
    commands.append(
        run(
            [
                sys.executable,
                "-c",
                "import handlers.refine; import systems.refine_system; print('[PASS] refine closure imports')",
            ]
        )
    )

    stage_commits = {
        message: commit_for_message(message) for message in REQUIRED_STAGE_MESSAGES
    }
    database = db_check()
    if (
        database["quick_check"] != "ok"
        or database["foreign_key_violations"]
        or database["total_changes"]
        or not database["unchanged"]
    ):
        raise RuntimeError("database closure invariant failed")

    report = {
        "stage": "18.20.2",
        "status": "CLOSED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "production_mutation": False,
        "balance_mutation": False,
        "manual_acceptance": {
            "status": "PASS",
            "reported_by_user": True,
            "verified": [
                "consecutive normal-stone attempts work without leaving the refine menu",
                "weapon refinement to +1 and +2 follows displayed 100 percent chances",
                "one enhancement stone is consumed for each real normal attempt",
                "success-rune refinement consumes exactly one stone and one success rune",
                "refine UI and result text are correct",
                "no new refine traceback observed",
            ],
            "accepted_runtime_note": (
                "A new Telegram callback has a new callback ID, while duplicate delivery of the same "
                "callback remains idempotent."
            ),
        },
        "root_causes_closed": [
            {
                "code": "REFINE_ATTEMPT_KEY_REUSED_INSIDE_EDITED_MESSAGE",
                "resolution": "idempotency key now uses user ID plus Telegram callback ID",
            },
            {
                "code": "REFINE_REPLAY_RENDERED_AS_FAILURE",
                "resolution": "idempotent replay has truthful material-preservation text",
            },
            {
                "code": "EXPIRED_REFINE_CALLBACK_CRASHED_POLLING",
                "resolution": "known expired or invalid callback-query acknowledgement is tolerated",
            },
        ],
        "authoritative_owners": {
            "transaction_and_balance": "systems/refine_system.py",
            "telegram_flow_and_rendering": "handlers/refine.py",
        },
        "invariants": {
            "balance_tables_changed": False,
            "new_attempt_key": "telegram:refine:<user_id>:<callback_id>",
            "same_callback_delivery": "same key and no duplicate resource consumption",
            "different_callback_delivery": "different key and a new real attempt",
            "transaction": "BEGIN IMMEDIATE with rollback, ownership and concurrency guards",
            "wal_shm_manipulated": False,
        },
        "verification": {
            "tests": list(TESTS),
            "commands": commands,
            "stage_commits": stage_commits,
        },
        "database": database,
        "known_nuances": [
            "The safe callback helper suppresses only Telegram errors whose text identifies an expired or invalid callback query.",
            "Other Telegram, database and runtime errors continue to propagate for diagnosis.",
            "Historical audit documentation stated that a stone was consumed during the false failure; later user observation corrected this: no stone was consumed because the operation was an idempotent replay.",
        ],
        "next_stage": "18.21.0 according to Stage 18 Roadmap v3 r3",
    }

    REPORT.parent.mkdir(exist_ok=True)
    MD.parent.mkdir(exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# Stage 18.20: Refine System Production Closure",
        "",
        "**Status:** CLOSED",
        "**Manual acceptance:** PASS",
        "**Production mutation in closure:** none",
        "**Refine balance mutation:** none",
        "",
        "## Closed defects",
        "",
        "- Consecutive attempts in one edited Telegram message no longer reuse the previous operation key.",
        "- A real attempt uses `telegram:refine:<user_id>:<callback_id>`.",
        "- Duplicate delivery of the same callback remains idempotent and never consumes materials twice.",
        "- An idempotent replay is no longer rendered as a failed refine attempt or as a new material consumption.",
        "- Expired or invalid refine callback acknowledgements no longer raise a polling traceback.",
        "",
        "## Authoritative ownership",
        "",
        "- `systems/refine_system.py` remains the canonical transaction, chance, roll and failure-policy owner.",
        "- `handlers/refine.py` remains the Telegram callback, preview and result-rendering owner.",
        "- No override or parallel refine implementation was introduced.",
        "",
        "## Balance preserved",
        "",
        "- Weapon and armor refine success tables were not changed.",
        "- Maximum refine levels, failure levels, material costs and refine effects were not changed.",
        "- A Success Rune still guarantees success and consumes one rune together with one Enhancement Stone.",
        "",
        "## Manual acceptance",
        "",
        "The user confirmed that refinement now works correctly. Consecutive normal attempts can refine to +1 and +2 without closing and reopening the menu. Correct materials are consumed, and Success Rune refinement works as expected.",
        "",
        "## Automated verification",
        "",
        "- Callback-ID idempotency and duplicate-delivery contracts: PASS.",
        "- Truthful replay rendering: PASS.",
        "- Expired callback-query guard: PASS.",
        "- Python compilation and runtime imports: PASS.",
        "- Canonical transaction and chance contracts: PASS.",
        "- `quick_check=ok`, foreign-key violations=0 and production database unchanged.",
        "- WAL/SHM were not manipulated.",
        "",
        "## Historical evidence correction",
        "",
        "The Stage 18.20.0 audit document recorded the first report as if the stone had been consumed during the false failure. Subsequent direct observation established that the stone was not consumed because the callback replayed an earlier attempt. This closure records the corrected evidence without rewriting the historical audit artifact.",
        "",
        "## Final decision",
        "",
        "Stage 18.20 is closed. Further refine changes require a separately identified runtime defect or an explicitly approved balance change.",
    ]
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "CLOSED",
                "tests": len(TESTS),
                "manual_acceptance": "PASS",
                "stage_18_20_1_commit": stage_commits["Stage 18.20.1"],
                "db_unchanged": True,
                "json": str(REPORT.relative_to(ROOT)),
                "md": str(MD.relative_to(ROOT)),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
