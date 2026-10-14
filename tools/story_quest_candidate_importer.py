#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic, non-activating importer for reviewed story-quest candidates.

This module maps candidate records into canonical ``StoryQuestDefinition``
objects and produces an import manifest. It deliberately does not import or
mutate ``data.story_quest_content.STORY_QUEST_REGISTRY``. Activation remains a
separate reviewed patch performed in approved packs of ten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

# Direct execution from ROM/tools sets sys.path[0] to ROM/tools rather than the
# project root. Insert the parent directory before importing canonical modules.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.story_quest_definitions import (
    NavigationDefinition,
    QuestItemDefinition,
    RequiredQuestItemDefinition,
    QuestType,
    RewardDefinition,
    StoryQuestDefinition,
    validate_story_quest_definition,
)
from data.story_quest_npcs import (
    resolve_story_quest_navigation,
    validate_story_quest_npc_references,
)

EXPECTED_SCHEMA_VERSION = 5
EXPECTED_QUEST_COUNT = 50
ALLOWED_CANDIDATE_FIELDS = frozenset({
    "quest_id", "number", "title", "quest_type", "location_id",
    "unlock_level", "previous_quest_id", "giver_npc_id", "turn_in_npc_id",
    "target_quantity", "description", "objective_text", "acceptance_text",
    "completion_text", "progress_text", "reward", "quest_item",
    "required_quest_items", "quest_item_consumption", "retain_until_quest_id",
    "boss_key", "next_route", "next_chapter", "encounter_paths",
    "guaranteed_call_after_success", "retry_after_defeat_or_escape",
    "boss_combat_reward_is_separate", "next_campaign_hint",
})
DEFERRED_RUNTIME_FIELDS = frozenset({
    "encounter_paths", "guaranteed_call_after_success",
    "retry_after_defeat_or_escape", "boss_combat_reward_is_separate",
})
PLANNING_ONLY_FIELDS = frozenset({"next_route", "next_chapter", "next_campaign_hint"})

class CandidateImportError(ValueError):
    """The reviewed candidate cannot be mapped deterministically and safely."""

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_candidate(path: Path) -> Mapping[str, Any]:
    """Load UTF-8 JSON without changing the ignored candidate file."""
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise CandidateImportError("unsupported candidate schema_version")
    if payload.get("production_authoritative") is not False:
        raise CandidateImportError("candidate must remain non-authoritative")
    quests = payload.get("quests")
    if not isinstance(quests, list) or len(quests) != EXPECTED_QUEST_COUNT:
        raise CandidateImportError("candidate must contain exactly 50 quests")
    return payload

def _optional_text(record: Mapping[str, Any], key: str, fallback: str) -> str:
    value = str(record.get(key) or "").strip()
    return value or fallback

def _map_reward(record: Mapping[str, Any]) -> RewardDefinition:
    reward = record.get("reward")
    if not isinstance(reward, Mapping):
        raise CandidateImportError(f"{record.get('quest_id')}: reward must be an object")
    exp = reward.get("exp")
    gold = reward.get("gold")
    if isinstance(exp, bool) or not isinstance(exp, int) or exp < 0:
        raise CandidateImportError(f"{record.get('quest_id')}: invalid EXP reward")
    if isinstance(gold, bool) or not isinstance(gold, (int, float)) or float(gold) < 0:
        raise CandidateImportError(f"{record.get('quest_id')}: invalid gold reward")
    return RewardDefinition(exp=exp, gold=round(float(gold), 2))

def build_item_consumers(quests: Sequence[Mapping[str, Any]]) -> dict[str, tuple[dict[str, Any], ...]]:
    """Index every later item prerequisite before mapping source quests.

    Candidate authors may omit ``retain_until_quest_id`` for a direct
    QUEST_ITEM -> TURN_IN pair. Runtime retention is therefore derived from the
    authoritative dependency graph, while an explicit marker must agree with
    the actual consuming quest.
    """
    consumers: dict[str, list[dict[str, Any]]] = {}
    for quest in quests:
        for required in quest.get("required_quest_items") or ():
            key = str(required.get("item_key") or "").strip()
            if not key:
                raise CandidateImportError(f"{quest.get('quest_id')}: required item key is empty")
            consumers.setdefault(key, []).append({
                "quest_id": str(quest.get("quest_id") or ""),
                "number": int(quest.get("number") or 0),
                "consume": bool(required.get("consume", True)),
            })
    return {key: tuple(values) for key, values in consumers.items()}


def _retention_contract(record: Mapping[str, Any], consumers: Mapping[str, Sequence[Mapping[str, Any]]]) -> tuple[bool, str | None]:
    item = record.get("quest_item") or {}
    key = str(item.get("item_key") or "").strip()
    source_number = int(record.get("number") or 0)
    later = [value for value in consumers.get(key, ()) if int(value["number"]) > source_number]
    consuming = [value for value in later if value["consume"]]
    explicit = record.get("retain_until_quest_id")
    if explicit and str(explicit) not in {value["quest_id"] for value in consuming}:
        raise CandidateImportError(f"{record.get('quest_id')}: retain_until_quest_id is not a later consuming quest")
    target = str(explicit) if explicit else (str(consuming[0]["quest_id"]) if consuming else None)
    return bool(later), target


def _map_item(record: Mapping[str, Any], consumers: Mapping[str, Sequence[Mapping[str, Any]]]) -> tuple[QuestItemDefinition | None, str | None]:
    item = record.get("quest_item")
    if item is None:
        return None, None
    if not isinstance(item, Mapping):
        raise CandidateImportError(f"{record.get('quest_id')}: quest_item must be an object")
    retained, target = _retention_contract(record, consumers)
    return QuestItemDefinition(
        item_key=str(item.get("item_key") or "").strip(),
        display_name=str(item.get("display_name") or "").strip(),
        required_quantity=int(item.get("required_quantity") or 0),
        drop_chance=float(item.get("drop_chance") or 0.0),
        consume_on_completion=not retained,
    ), target


def _map_required_items(record: Mapping[str, Any]) -> tuple[RequiredQuestItemDefinition, ...]:
    """Map TALK/TURN_IN prerequisites without inventing inventory semantics."""
    values = record.get("required_quest_items") or ()
    if not isinstance(values, (list, tuple)):
        raise CandidateImportError(f"{record.get('quest_id')}: required_quest_items must be a list")
    return tuple(
        RequiredQuestItemDefinition(
            item_key=str(item.get("item_key") or "").strip(),
            quantity=int(item.get("quantity") or 0),
            consume=bool(item.get("consume", True)),
        )
        for item in values
    )

def map_candidate_record(record: Mapping[str, Any], consumers: Mapping[str, Sequence[Mapping[str, Any]]]) -> tuple[StoryQuestDefinition, dict[str, Any]]:
    """Map one record to canonical schema plus separately classified metadata."""
    unknown = sorted(set(record) - ALLOWED_CANDIDATE_FIELDS)
    if unknown:
        raise CandidateImportError(f"{record.get('quest_id')}: unknown fields: {unknown}")
    quest_id = str(record.get("quest_id") or "").strip()
    giver = str(record.get("giver_npc_id") or "").strip()
    turn_in_raw = record.get("turn_in_npc_id")
    turn_in = None if turn_in_raw is None else str(turn_in_raw).strip() or None
    validate_story_quest_npc_references(giver_npc_id=giver, turn_in_npc_id=turn_in)
    route = resolve_story_quest_navigation(turn_in or giver)
    objective = str(record.get("objective_text") or "").strip()
    mapped_item, retention_target = _map_item(record, consumers)
    definition = StoryQuestDefinition(
        quest_id=quest_id,
        number=int(record.get("number") or 0),
        title=str(record.get("title") or "").strip(),
        quest_type=QuestType(str(record.get("quest_type") or "")),
        location_id=str(record.get("location_id") or "").strip(),
        unlock_level=int(record.get("unlock_level") or 0),
        previous_quest_id=record.get("previous_quest_id"),
        giver_npc_id=giver,
        turn_in_npc_id=turn_in,
        description=str(record.get("description") or "").strip(),
        objective_text=objective,
        target_quantity=int(record.get("target_quantity") or 0),
        boss_key=record.get("boss_key"),
        quest_item=mapped_item,
        required_quest_items=_map_required_items(record),
        quest_item_consumption=str(record.get("quest_item_consumption") or "default"),
        reward=_map_reward(record),
        navigation=NavigationDefinition(
            location_id=str(record.get("location_id") or "").strip(),
            giver_npc_id=giver,
            turn_in_npc_id=turn_in,
            objective_hint=objective,
            next_step_hint=route["route_text"],
        ),
    )
    validate_story_quest_definition(definition)
    metadata = {
        "acceptance_text": _optional_text(record, "acceptance_text", definition.description),
        "completion_text": _optional_text(record, "completion_text", definition.objective_text),
        "progress_text": str(record.get("progress_text") or "").strip(),
        "deferred_runtime": {key: record[key] for key in sorted(DEFERRED_RUNTIME_FIELDS & set(record))},
        "planning_only": {key: record[key] for key in sorted(PLANNING_ONLY_FIELDS & set(record))},
        "retention_target_quest_id": retention_target,
    }
    return definition, metadata

def build_import_manifest(payload: Mapping[str, Any], source_path: Path) -> dict[str, Any]:
    """Build a stable manifest while preserving strict sequential chain checks."""
    definitions = []
    content = {}
    deferred = {}
    previous_id = None
    consumers = build_item_consumers(payload["quests"])
    retention_contracts = {}
    seen_ids = set()
    seen_numbers = set()
    seen_items = set()
    for expected_number, record in enumerate(payload["quests"], start=1):
        definition, metadata = map_candidate_record(record, consumers)
        if definition.number != expected_number:
            raise CandidateImportError("quest numbers must be exactly 1..50")
        if definition.previous_quest_id != previous_id:
            raise CandidateImportError(f"{definition.quest_id}: invalid predecessor")
        if definition.quest_id in seen_ids or definition.number in seen_numbers:
            raise CandidateImportError("duplicate quest identity")
        if definition.quest_item:
            if definition.quest_item.item_key in seen_items:
                raise CandidateImportError("duplicate quest item key")
            seen_items.add(definition.quest_item.item_key)
        definitions.append(asdict(definition))
        content[definition.quest_id] = {
            "acceptance_text": metadata["acceptance_text"],
            "completion_text": metadata["completion_text"],
            "progress_text": metadata["progress_text"],
        }
        if metadata["deferred_runtime"]:
            deferred[definition.quest_id] = metadata["deferred_runtime"]
        if definition.quest_item is not None:
            retention_contracts[definition.quest_id] = {
                "item_key": definition.quest_item.item_key,
                "consume_on_completion": definition.quest_item.consume_on_completion,
                "target_quest_id": metadata["retention_target_quest_id"],
            }
        previous_id = definition.quest_id
        seen_ids.add(definition.quest_id)
        seen_numbers.add(definition.number)
    canonical = json.dumps({"definitions": definitions, "content": content, "deferred_runtime": deferred}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": 1,
        "source_path": source_path.as_posix(),
        "source_sha256": _sha256(source_path),
        "quest_count": len(definitions),
        "quest_item_count": len(seen_items),
        "retention_contracts": retention_contracts,
        "definition_ids": [item["quest_id"] for item in definitions],
        "mapped_definition_count": len(definitions),
        "mapped_content_count": len(content),
        "deferred_runtime_quest_ids": sorted(deferred),
        "deferred_runtime_fields": sorted({key for value in deferred.values() for key in value}),
        "activation_batches": [[1,10],[11,20],[21,30],[31,40],[41,50]],
        "production_activation_performed": False,
        "runtime_registry_mutated": False,
        "canonical_payload_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }

def verify_manifest(manifest: Mapping[str, Any], expected_source_sha256: str | None = None) -> None:
    """Fail closed unless the manifest proves a full, non-activating mapping."""
    if manifest.get("quest_count") != 50 or manifest.get("mapped_definition_count") != 50:
        raise CandidateImportError("manifest does not cover all 50 definitions")
    if manifest.get("mapped_content_count") != 50:
        raise CandidateImportError("manifest does not cover all 50 content records")
    if manifest.get("production_activation_performed") is not False:
        raise CandidateImportError("importer must not activate production content")
    if manifest.get("runtime_registry_mutated") is not False:
        raise CandidateImportError("importer must not mutate runtime registry")
    if expected_source_sha256 and manifest.get("source_sha256") != expected_source_sha256:
        raise CandidateImportError("candidate SHA-256 mismatch")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    payload = load_candidate(args.candidate)
    manifest = build_import_manifest(payload, args.candidate)
    verify_manifest(manifest, args.expected_sha256)
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
