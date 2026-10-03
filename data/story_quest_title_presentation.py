#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical presentation-title policy for spoiler-safe story quest UI."""
from __future__ import annotations
from types import MappingProxyType
from data.story_quest_definitions import QuestType

PRE_REVEAL_TITLE_BY_QUEST_ID = MappingProxyType({'start_path_004_guard_uniform_scrap': 'Слід патруля', 'start_path_007_broken_guard_lantern': 'Знахідка біля мосту', 'start_path_013_runic_crystal_fragment': 'Матеріальний слід аномалії', 'start_path_019_guards_note': 'Слід зниклого патруля', 'start_path_023_guards_ring': 'Особиста річ вартового', 'start_path_029_torn_guard_cloak': 'Слід нападу', 'start_path_034_runemarked_wolf_pelt': 'Матеріал для Коваля', 'start_path_043_pack_leader_seal': 'Незвичайна мітка', 'start_path_046_pack_leader_fur': 'Матеріал зі слідом Ватажка'})


def resolve_story_quest_presentation_title(quest, status: str, quest_item_quantity: int = 0) -> str:
    """Return a neutral title until a hidden quest item is actually acquired."""
    if quest.quest_type is not QuestType.QUEST_ITEM:
        return str(quest.title)
    state = str(status or "LOCKED").upper()
    if state in {"COMPLETED", "SKIPPED"}:
        return str(quest.title)
    item = quest.quest_item
    required = int(item.required_quantity) if item is not None else int(quest.target_quantity)
    if int(quest_item_quantity or 0) >= max(1, required):
        return str(quest.title)
    return str(PRE_REVEAL_TITLE_BY_QUEST_ID.get(quest.quest_id, quest.title))
