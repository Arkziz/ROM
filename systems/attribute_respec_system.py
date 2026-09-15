#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""Canonical Attribute Respec domain service. UI integration is intentionally separate."""

from __future__ import annotations

from datetime import datetime,timezone

REBIRTH_SPHERE_ITEM_ID=504
NEW_PATH_SPHERE_ITEM_ID=501

ALLOCATED=("allocated_strength","allocated_dexterity","allocated_intelligence","allocated_wisdom","allocated_stamina")

class AttributeRespecError(RuntimeError):pass

class RespecNotAvailableError(AttributeRespecError):pass

class RespecStateChangedError(AttributeRespecError):pass

class RespecAlreadyProcessed(AttributeRespecError):pass

def _db(db_module=None):

 if db_module is not None:return db_module

 import db;return db

def _row(cursor,user_id):

 return cursor.execute("""SELECT character_class,free_attribute_points,total_attribute_points_earned,

 allocated_strength,allocated_dexterity,allocated_intelligence,allocated_wisdom,allocated_stamina,

 hp,mp FROM users WHERE user_id=?""",(int(user_id),)).fetchone()

def _value(row,index):return int((row[index] if row is not None else 0) or 0)

def get_attribute_respec_preview(user_id,*,db_module=None):

 database=_db(db_module);row=_row(database.cursor,user_id)

 if not row:raise AttributeRespecError(f"Player not found: {user_id}")

 allocated={"strength":_value(row,3),"dexterity":_value(row,4),"intelligence":_value(row,5),"wisdom":_value(row,6),"stamina":_value(row,7)}

 returned=sum(allocated.values());earned=_value(row,2);free=_value(row,1)

 if earned!=free+returned:raise AttributeRespecError("Attribute point invariant failed")

 return {"user_id":int(user_id),"character_class":str(row[0] or ""),"allocated":allocated,"returned_points":returned,"free_before":free,"free_after":free+returned,"total_attribute_points_earned":earned}

def reset_allocated_attributes(user_id,source_inventory_id,idempotency_key,*,operation_type="attribute_respec",new_class=None,expected_item_id=None,db_module=None,max_hp_getter=None,max_mp_getter=None,availability_guard=None):

 if operation_type not in ("attribute_respec","class_change"):raise AttributeRespecError("Unsupported operation type")

 key=str(idempotency_key or "").strip()

 if not key:raise AttributeRespecError("idempotency_key is required")

 database=_db(db_module);conn=database.conn;cursor=database.cursor

 if conn.in_transaction:raise AttributeRespecError("Respec requires transaction ownership")

 conn.execute("BEGIN IMMEDIATE")

 try:

  existing=cursor.execute("SELECT id FROM attribute_respec_events WHERE idempotency_key=?",(key,)).fetchone()

  if existing:raise RespecAlreadyProcessed("Respec confirmation already processed")

  if availability_guard:

   guard=availability_guard(int(user_id),cursor)

   if guard is not True:raise RespecNotAvailableError(str(guard or "Character is busy"))

  before=get_attribute_respec_preview(user_id,db_module=database)

  if operation_type=="attribute_respec" and before["returned_points"]<=0:raise RespecNotAvailableError("No allocated attribute points")

  inv=cursor.execute("SELECT item_id,quantity FROM inventory WHERE id=? AND user_id=?",(int(source_inventory_id),int(user_id))).fetchone()

  expected_item_id = int(expected_item_id or (NEW_PATH_SPHERE_ITEM_ID if operation_type=="class_change" else REBIRTH_SPHERE_ITEM_ID))
  if not inv or int(inv[0])!=expected_item_id:raise RespecNotAvailableError("Required sphere not found")

  quantity=int(inv[1] or 0)

  cursor.execute("""UPDATE users SET free_attribute_points=free_attribute_points+?,

   allocated_strength=0,allocated_dexterity=0,allocated_intelligence=0,

   allocated_wisdom=0,allocated_stamina=0 WHERE user_id=?""",(before["returned_points"],int(user_id)))

  if operation_type=="class_change":cursor.execute("UPDATE users SET character_class=? WHERE user_id=?",(str(new_class or ""),int(user_id)))

  if quantity<=1:cursor.execute("DELETE FROM inventory WHERE id=? AND user_id=?",(int(source_inventory_id),int(user_id)))

  else:cursor.execute("UPDATE inventory SET quantity=quantity-1 WHERE id=? AND user_id=?",(int(source_inventory_id),int(user_id)))

  from db_modules.inventory import compact_user_item_stacks

  compact_user_item_stacks(user_id,expected_item_id,commit=False,connection=conn)

  hp_before=_value(_row(cursor,user_id),8);mp_before=_value(_row(cursor,user_id),9)

  max_hp=int(max_hp_getter(int(user_id)) if max_hp_getter else hp_before)

  max_mp=int(max_mp_getter(int(user_id)) if max_mp_getter else mp_before)

  cursor.execute("UPDATE users SET hp=MIN(COALESCE(hp,0),?),max_hp=?,mp=MIN(COALESCE(mp,0),?),max_mp=? WHERE user_id=?",(max_hp,max_hp,max_mp,max_mp,int(user_id)))

  a=before["allocated"]

  cursor.execute("""INSERT INTO attribute_respec_events(user_id,operation_type,old_class,new_class,returned_points,

   returned_strength,returned_dexterity,returned_intelligence,returned_wisdom,returned_stamina,

   source_inventory_id,source_item_id,idempotency_key,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",

   (int(user_id),operation_type,before["character_class"],new_class,before["returned_points"],a["strength"],a["dexterity"],a["intelligence"],a["wisdom"],a["stamina"],int(source_inventory_id),expected_item_id,key,datetime.now(timezone.utc).isoformat()))

  after=get_attribute_respec_preview(user_id,db_module=database);conn.commit()

  return {"success":True,"before":before,"after":after,"max_hp":max_hp,"max_mp":max_mp}

 except Exception:

  conn.rollback();raise

