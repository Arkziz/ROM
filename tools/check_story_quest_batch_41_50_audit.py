#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
CANDIDATE=ROOT/'Квести/ROM_квести_Початок_Шляху_candidate.json'
def sha(path):
 h=hashlib.sha256();h.update(path.read_bytes());return h.hexdigest()
assert sha(CANDIDATE)=='6d7115478f2f1119376490b449b60034532a8b89be07633f4692337f8bf0c154'
from data.story_quest_content import STORY_QUEST_REGISTRY
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,41))
assert all(q.number<41 for q in STORY_QUEST_REGISTRY.values())
for rel in ("data/bosses.py","systems/boss_system.py"):
 assert (ROOT/rel).exists(),rel
report=json.loads((ROOT/'reports/stage_19_27_1_story_quest_batch_41_50_audit.json').read_text(encoding="utf-8"))
assert [q["number"] for q in report["candidate_quests"]]==list(range(41,51))
assert report["production_mutation"] is False and report["database_mutation"] is False
assert report["boss_audit"]["canonical_policy_expected"].startswith("boss is encountered through the normal Hunt pipeline")
print("STORY QUEST BATCH 41-50 AUDIT: PASS")
