#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def sha(path):
 h=hashlib.sha256();h.update(path.read_bytes());return h.hexdigest()
expected=json.loads('{"data/bosses.py": "08013d3a763ce8193762e181329abb4643b3544a2d52090574975b1df7478102", "data/story_quest_content.py": "1fc2147764ddb2d88229bb659f2e3f4c4833327235e9b1ed2fe29acaabd43637", "handlers/story_quest_npc_runtime.py": "63d82dc89663bb1e4c804382b0284d29cb1af371b09edf420ce555e050bd70be", "systems/boss_system.py": "3dab65e3229c1653b4be5bb5e47c39a479d7f602f3cdb38d807aa30416bedd2a"}')
for rel,value in expected.items():
 assert sha(ROOT/rel)==value,(rel,sha(ROOT/rel),value)
from data.story_quest_content import STORY_QUEST_REGISTRY
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,41))
report=json.loads((ROOT/'reports/stage_19_27_2_story_boss_invocation_adapter_audit.json').read_text(encoding="utf-8"))
assert report["production_mutation"] is False
assert report["candidate_mutation"] is False
assert report["database_mutation"] is False
assert report["recommended_contract"]["surface"]=="look_around_inline"
assert report["recommended_contract"]["permanent_reply_button"] is False
assert report["recommended_contract"]["random_hunt_encounter_remains_enabled"] is True
assert all(value<=64 for value in report["callback_samples_utf8_bytes"].values())
print("STORY BOSS INVOCATION ADAPTER AUDIT: PASS")
