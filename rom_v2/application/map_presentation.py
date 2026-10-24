"""Pure localized Map Presentation DTOs and callback codec."""
from __future__ import annotations
import math
from dataclasses import dataclass
from datetime import datetime,timezone
from enum import StrEnum
from rom_v2.content.location_catalog import is_location_unlocked
from rom_v2.content.world_graph import CITY_NODE_ID,get_adjacent_nodes,get_world_node
UNKNOWN_PLACE="🧭 Невідома місцевість"
class MapMode(StrEnum):READY="ready";IN_TRANSIT="in_transit"
@dataclass(frozen=True,slots=True)
class MapAction:
 kind:str;label:str;callback_data:str;enabled:bool=True
@dataclass(frozen=True,slots=True)
class DirectionView:
 node_id:str;label:str;unlocked:bool;action:MapAction|None
@dataclass(frozen=True,slots=True)
class ActiveTravelView:
 travel_id:int;revision:int;from_label:str;to_label:str;remaining_seconds:int;cancel:MapAction
@dataclass(frozen=True,slots=True)
class MapView:
 mode:MapMode;current_node_id:str;current_label:str;directions:tuple[DirectionView,...];actions:tuple[MapAction,...];active_travel:ActiveTravelView|None=None
@dataclass(frozen=True,slots=True)
class CallbackCommand:
 action:str;node_id:str|None=None;travel_id:int|None=None;revision:int|None=None

def node_label(node_id):
 node=get_world_node(str(node_id or "").strip())
 return node.name if node else UNKNOWN_PLACE

def encode_callback(command):
 if command.action in {"open","players"} and not any((command.node_id,command.travel_id,command.revision)):return f"map:{command.action}"
 if command.action in {"info","preview","start"} and command.node_id and get_world_node(command.node_id):return f"map:{command.action}:{command.node_id}"
 if command.action=="cancel" and command.travel_id and command.revision:return f"map:cancel:{command.travel_id}:{command.revision}"
 raise ValueError("invalid callback command")

def decode_callback(payload):
 parts=str(payload or "").split(":")
 try:
  if parts==["map","open"]:return CallbackCommand("open")
  if parts==["map","players"]:return CallbackCommand("players")
  if len(parts)==3 and parts[0]=="map" and parts[1] in {"info","preview","start"} and get_world_node(parts[2]):return CallbackCommand(parts[1],node_id=parts[2])
  if len(parts)==4 and parts[:2]==["map","cancel"] and int(parts[2])>0 and int(parts[3])>0:return CallbackCommand("cancel",travel_id=int(parts[2]),revision=int(parts[3]))
 except (TypeError,ValueError):pass
 return None

def build_map_view(current_node_id,player_level,*,active_travel=None,now=None):
 current=str(current_node_id or "").strip();label=node_label(current)
 if active_travel is not None:
  moment=(now or datetime.now(timezone.utc)).astimezone(timezone.utc);arrival=active_travel.arrival_at.astimezone(timezone.utc)
  remaining=max(0,math.ceil((arrival-moment).total_seconds()))
  cancel=MapAction("cancel","❌ Скасувати подорож",encode_callback(CallbackCommand("cancel",travel_id=active_travel.travel_id,revision=active_travel.revision)))
  trip=ActiveTravelView(active_travel.travel_id,active_travel.revision,node_label(active_travel.from_node),node_label(active_travel.to_node),remaining,cancel)
  return MapView(MapMode.IN_TRANSIT,current,label,(),(MapAction("open","🔄 Оновити","map:open"),),trip)
 directions=[]
 for target in get_adjacent_nodes(current):
  unlocked=target==CITY_NODE_ID or is_location_unlocked(target,player_level)
  action=MapAction("preview",f"➡️ {node_label(target)}",encode_callback(CallbackCommand("preview",node_id=target))) if unlocked else None
  directions.append(DirectionView(target,node_label(target),unlocked,action))
 return MapView(MapMode.READY,current,label,tuple(directions),(MapAction("open","🔄 Оновити","map:open"),MapAction("players","👥 Гравці поруч","map:players")))
