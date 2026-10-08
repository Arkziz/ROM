#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from handlers.story_quest_hierarchy_ui import build_story_index,build_section_index,build_section_quests,PROFILE_CALLBACK

def labels(markup):return [(b.text,b.callback_data) for row in markup.keyboard for b in row]
# Root has an explicit canonical Profile return.
text,kb=build_story_index(1,lambda u,q:'locked');assert ('🔙 До профілю',PROFILE_CALLBACK) in labels(kb);assert PROFILE_CALLBACK=='story_quest:profile'
# Every status family receives its canonical icon.
icons={'completed':'✅','active':'📖','available':'✨','locked':'🔒','skipped':'⏭️'}
for status,icon in icons.items():
 reader=lambda u,q,s=status:s
 _,sections=build_section_index('dark_forest',1,reader);_,quests=build_section_quests('dark_forest_05',1,reader,lambda u,q:q.title)
 all_labels='\n'.join(x[0] for x in labels(sections)+labels(quests));assert icon in all_labels,(status,all_labels)
# Mixed finalized section is ⏭️, while count includes only completed quests.
def mixed(u,q):return 'completed' if q.number in (91,92,93) else 'skipped'
_,sections=build_section_index('dark_forest',1,mixed);section_label=next(text for text,data in labels(sections) if data=='sqh:v1:sec:dark_forest_05');assert section_label.startswith('⏭️ ') and section_label.endswith('· 3/10'),section_label
_,quests=build_section_quests('dark_forest_05',1,mixed,lambda u,q:q.title);quest_labels=[text for text,data in labels(quests) if data and data.startswith('sqh:v1:q:')];assert sum(x.startswith('✅ ') for x in quest_labels)==3 and sum(x.startswith('⏭️ ') for x in quest_labels)==7
# A partially skipped but still locked section remains 🔒 until fully finalized.
def unfinished(u,q):return 'skipped' if q.number==91 else 'locked'
_,sections=build_section_index('dark_forest',1,unfinished);label=next(text for text,data in labels(sections) if data=='sqh:v1:sec:dark_forest_05');assert label.startswith('🔒 ') and label.endswith('· 0/10')
print('PASS: Stage 19.36.2')
