#!/usr/bin/env python3
import inspect,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_definitions import derive_story_quest_status,DerivedQuestStatus
from handlers.story_quests import build_story_quest_journal_keyboard
from handlers import story_quest_npc_runtime as runtime
from systems import story_quest_system
assert derive_story_quest_status(persistent_status=None,player_level=2,unlock_level=2,predecessor_completed=True,another_active_quest=False)==DerivedQuestStatus.AVAILABLE
src=inspect.getsource(story_quest_system)
assert 'SKIPPED' in src and ('predecessor' in src.lower() or 'previous' in src.lower())
kb=build_story_quest_journal_keyboard(page=1,has_previous=True,has_next=True)
labels=[b['text'] for row in kb for b in row]
assert '⬅️ Назад' in labels and '➡️ Далі' in labels and '◀️' not in labels and '▶️' not in labels
assert runtime.NPC_BUTTONS.get('💠 Рунний Майстер')=='rune_master'
from handlers import runes
assert "send_story_npc_if_present(bot, message, 'rune_master')" in inspect.getsource(runes)
print('QUEST 11 AVAILABILITY AND PAGINATION: PASS')
