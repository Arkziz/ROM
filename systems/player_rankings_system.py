# -*- coding: utf-8 -*-
"""Read-only player rankings: top 100, 20 per page, deterministic ordering."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from data.player_progression import get_exp_to_next_level
DB_PATH=Path(__file__).resolve().parents[1]/'game.db'
TOP_LIMIT=100
PAGE_SIZE=20
RANKING_CATEGORIES={
 'total_exp':{'label':'⭐ Загальний досвід','value_label':'Досвід'},
 'gold':{'label':'💰 Золото','value_label':'Золото'},
 'str':{'label':'💪 Сила','value_label':'Сила'},
 'sta':{'label':'🛡️ Витривалість','value_label':'Витривалість'},
 'dex':{'label':'🏹 Спритність','value_label':'Спритність'},
 'intelligence':{'label':'🔮 Інтелект','value_label':'Інтелект'},
 'wis':{'label':'📘 Мудрість','value_label':'Мудрість'},
}
def calculate_cumulative_player_exp(level,current_exp):
 level=max(1,int(level or 1));return sum(int(get_exp_to_next_level(n)) for n in range(1,level))+max(0,int(current_exp or 0))
def get_player_ranking_categories():return {key:dict(value) for key,value in RANKING_CATEGORIES.items()}
def _connect(path=None):
 c=sqlite3.connect(str(path or DB_PATH),timeout=30);c.row_factory=sqlite3.Row;c.execute('PRAGMA query_only=ON');c.execute('PRAGMA busy_timeout=30000');return c
def _eligible(c):
 rows=c.execute("SELECT user_id,character_name,level,exp,gold,str,sta,dex,intelligence,wis FROM users WHERE TRIM(COALESCE(character_name,''))<>''").fetchall();result=[]
 for row in rows:
  item=dict(row);item['total_exp']=calculate_cumulative_player_exp(item['level'],item['exp']);result.append(item)
 return result
def _ranked(rows,key):
 if key=='total_exp':rows.sort(key=lambda x:(-int(x['total_exp']),int(x['user_id'])))
 else:rows.sort(key=lambda x:(-float(x.get(key) or 0),-int(x.get('level') or 1),int(x['user_id'])))
 for index,row in enumerate(rows,1):row['position']=index;row['value']=row['total_exp'] if key=='total_exp' else row.get(key)
 return rows
def get_player_ranking_page(ranking_key,viewer_user_id,page=0,page_size=PAGE_SIZE,top_limit=TOP_LIMIT,db_path=None):
 key=str(ranking_key or '').strip().lower()
 if key not in RANKING_CATEGORIES:return {'success':False,'message':'❌ Невідома категорія рейтингу.'}
 size=max(1,min(PAGE_SIZE,int(page_size or PAGE_SIZE)));limit=max(1,min(TOP_LIMIT,int(top_limit or TOP_LIMIT)));page=max(0,int(page or 0));c=_connect(db_path)
 try:ranked=_ranked(_eligible(c),key)
 finally:c.close()
 top=ranked[:limit];pages=max(1,(len(top)+size-1)//size);page=min(page,pages-1);start=page*size;items=top[start:start+size];viewer=next((dict(row) for row in ranked if int(row['user_id'])==int(viewer_user_id)),None)
 return {'success':True,'ranking_key':key,'category':dict(RANKING_CATEGORIES[key]),'items':items,'page':page,'page_size':size,'pages':pages,'top_limit':limit,'total_eligible':len(ranked),'has_previous':page>0,'has_next':page+1<pages,'viewer':viewer,'viewer_on_page':bool(viewer and any(int(x['user_id'])==int(viewer_user_id) for x in items))}
def get_player_ranking_position(ranking_key,user_id,db_path=None):
 data=get_player_ranking_page(ranking_key,user_id,0,PAGE_SIZE,TOP_LIMIT,db_path);return data.get('viewer') if data.get('success') else None
