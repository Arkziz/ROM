#!/usr/bin/env python3
"""Verify the ROM V2 domain-event contract without importing runtime code."""
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {
    "event_id", "event_key", "aggregate_type", "aggregate_id", "aggregate_version",
    "sequence", "occurred_at_utc", "payload", "correlation_id", "causation_id", "schema_version",
}
EVENT_CLASS_RE = re.compile(r"(?i)^(domainevent|eventenvelope|eventrecord)$")
PRESENTATION_ROOTS = {"aiogram", "telebot", "telegram"}
DATABASE_ROOTS = {"sqlite3", "sqlalchemy", "aiosqlite"}


def verify(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    fields = set(contract.get("event_type", {}).get("fields", {}))
    if fields != REQUIRED_FIELDS:
        violations.append({"rule": "EVENT_FIELD_SET", "missing": sorted(REQUIRED_FIELDS-fields), "extra": sorted(fields-REQUIRED_FIELDS)})
    if contract.get("canonical_owner") != "rom_v2.domain.events":
        violations.append({"rule": "CANONICAL_OWNER"})
    naming = contract.get("naming", {})
    if naming.get("event_key_format") != "lowercase_dot_separated_past_tense" or not naming.get("localized_text_forbidden"):
        violations.append({"rule": "STABLE_EVENT_NAMING"})
    ordering = contract.get("ordering", {})
    if ordering.get("primary_order") != ["aggregate_version", "sequence"]:
        violations.append({"rule": "EVENT_ORDERING"})
    if not ordering.get("occurred_at_utc_not_an_ordering_authority"):
        violations.append({"rule": "TIMESTAMP_NOT_ORDERING_AUTHORITY"})
    persistence = contract.get("persistence", {})
    for key in ("append_only", "inside_same_unit_of_work_as_state_change", "publish_after_commit", "rollback_discards_uncommitted_events", "outbox_required_for_external_delivery", "consumer_idempotency_required", "restart_reloads_unpublished_outbox"):
        if not persistence.get(key): violations.append({"rule": "PERSISTENCE_INVARIANT", "key": key})
    presentation = contract.get("presentation", {})
    if presentation.get("domain_event_contains_presentation") or not presentation.get("telegram_types_forbidden"):
        violations.append({"rule": "PRESENTATION_SEPARATION"})
    integration = contract.get("error_integration", {})
    if integration.get("failed_operation_persists_events") or integration.get("idempotent_repeat_emits_duplicate_event"):
        violations.append({"rule": "RESULT_EVENT_INTEGRATION"})

    owners: list[dict[str, Any]] = []
    forbidden_imports: list[dict[str, Any]] = []
    rom_v2 = root / "rom_v2"
    if rom_v2.is_dir():
        for path in sorted(rom_v2.rglob("*.py")):
            text = path.read_text(encoding="utf-8", errors="replace")
            try: tree = ast.parse(text, filename=str(path))
            except SyntaxError as exc:
                violations.append({"rule": "PARSE_ERROR", "file": path.relative_to(root).as_posix(), "error": str(exc)}); continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and EVENT_CLASS_RE.fullmatch(node.name):
                    owners.append({"file": path.relative_to(root).as_posix(), "class": node.name, "line": node.lineno})
                if path.relative_to(root).as_posix().startswith("rom_v2/domain/"):
                    modules=[]
                    if isinstance(node, ast.Import): modules=[a.name for a in node.names]
                    elif isinstance(node, ast.ImportFrom): modules=[node.module or ""]
                    for module in modules:
                        top=module.split(".")[0]
                        if top in PRESENTATION_ROOTS|DATABASE_ROOTS:
                            forbidden_imports.append({"file":path.relative_to(root).as_posix(),"line":node.lineno,"import":module})
    if len(owners)>1: violations.append({"rule":"MULTIPLE_EVENT_OWNERS","owners":owners})
    if owners and owners[0]["file"]!="rom_v2/domain/events.py": violations.append({"rule":"WRONG_EVENT_OWNER","owners":owners})
    if forbidden_imports: violations.append({"rule":"DOMAIN_FRAMEWORK_OR_DB_IMPORT","imports":forbidden_imports})
    return {"schema_version":1,"summary":{"status":"PASS" if not violations else "FAIL","required_field_count":len(fields),"physical_event_owner_count":len(owners),"forbidden_domain_import_count":len(forbidden_imports),"violation_count":len(violations),"physical_event_model_exists":bool(owners)},"event_owners":owners,"forbidden_domain_imports":forbidden_imports,"violations":violations}


def main() -> int:
    p=argparse.ArgumentParser();p.add_argument("--project-root",default=".");p.add_argument("--contract",required=True);p.add_argument("--json-out");a=p.parse_args()
    result=verify(Path(a.project_root).resolve(),json.loads(Path(a.contract).read_text(encoding="utf-8")))
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if a.json_out:Path(a.json_out).write_text(text,encoding="utf-8",newline="\n")
    print(f"V2 domain-event verifier: {result['summary']['status']}");print(f"Fields: {result['summary']['required_field_count']}");print(f"Physical event owners: {result['summary']['physical_event_owner_count']}");print(f"Forbidden domain imports: {result['summary']['forbidden_domain_import_count']}");print(f"Violations: {result['summary']['violation_count']}")
    return 0 if result["summary"]["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
