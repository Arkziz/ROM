#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Production-shaped regression for candidate chained-item retention."""
from __future__ import annotations
import argparse,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_definitions import QuestType
from systems.story_quest_completion_system import complete_active_story_quest
from tools.story_quest_candidate_importer import build_import_manifest,load_candidate,map_candidate_record,build_item_consumers
EXPECTED=((4,5),(7,8),(13,14),(15,16),(19,20),(23,30),(26,30),(29,30),(34,35),(37,38),(43,44),(46,47))
def schema(c):c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY,level INTEGER,exp INTEGER,gold REAL);CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));")
def reward(**kw):return {'ok':True}
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();payload=load_candidate(a.candidate);cons=build_item_consumers(payload['quests']);defs={};meta={}
 for r in payload['quests']:
  d,m=map_candidate_record(r,cons);defs[d.number]=d;meta[d.number]=m
 actual=[]
 for source,target in EXPECTED:
  d=defs[source];assert d.quest_type is QuestType.QUEST_ITEM and d.quest_item and not d.quest_item.consume_on_completion;assert meta[source]['retention_target_quest_id']==defs[target].quest_id;assert any(x.item_key==d.quest_item.item_key and x.consume for x in defs[target].required_quest_items);actual.append((source,target))
 manifest=build_import_manifest(payload,a.candidate);assert len(manifest['retention_contracts'])==12
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;schema(c);c.execute('INSERT INTO users VALUES(1,1,0,0.0)');source,target=defs[4],defs[5];c.execute("INSERT INTO user_story_quests VALUES(?,?, 'ACTIVE',0,1,0,'','','','')",(1,source.quest_id));c.execute('INSERT INTO user_story_quest_items VALUES(1,?,?,1,\'1\')',(source.quest_id,source.quest_item.item_key));c.commit();complete_active_story_quest(c,registry={source.quest_id:source},user_id=1,quest_id=source.quest_id,reward_adapter=reward,expected_turn_in_npc_id=source.turn_in_npc_id);assert c.execute('SELECT quantity FROM user_story_quest_items WHERE item_key=?',(source.quest_item.item_key,)).fetchone()[0]==1
 c.execute("DELETE FROM user_story_quests");c.execute("INSERT INTO user_story_quests VALUES(?,?, 'ACTIVE',0,1,0,'','','','')",(1,target.quest_id));c.commit();complete_active_story_quest(c,registry={target.quest_id:target},user_id=1,quest_id=target.quest_id,reward_adapter=reward,expected_turn_in_npc_id=target.turn_in_npc_id);assert c.execute('SELECT COUNT(*) FROM user_story_quest_items WHERE item_key=?',(source.quest_item.item_key,)).fetchone()[0]==0
 print('CHAINED QUEST ITEM RETENTION: PASS');print(json.dumps(actual));return 0
if __name__=='__main__':raise SystemExit(main())
