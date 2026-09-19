from __future__ import annotations
from collections import defaultdict
from typing import Any
from data.runes import get_rune_definition

SLOT_UK={"main_hand":"Основна рука","off_hand":"Друга рука","helmet":"Шолом","shoulders":"Наплічники","chest":"Нагрудник","gloves":"Рукавички","legs":"Поножі","boots":"Чоботи","necklace":"Намисто","ring":"Перстень"}
ARMOR_UK={"cloth":"тканина","leather":"шкіра","chain":"кольчуга","plate":"лати","":""}
RARITY_UK={"common":"білий","uncommon":"зелений","rare":"синій","epic":"фіолетовий"}
STATIC_UK={108:"Трофей моба",401:"Мале зілля здоров'я",402:"Велике зілля здоров'я",403:"Мале зілля мани",404:"Велике зілля мани",601:"Камінь Посилення",726:"Жетон Фіріуса"}

def item_name_uk(item_id:int|None,name:str,category:str,rarity:str="common",slot_key:str="",item_level:int=1,armor_type:str="")->str:
    if item_id is not None and 701<=int(item_id)<=725:
        rune=get_rune_definition(int(item_id));return str(rune.get("name",name))
    if int(item_id or 0) in STATIC_UK:return STATIC_UK[int(item_id)]
    if category=="equipment":
        slot=SLOT_UK.get(slot_key,slot_key or "Спорядження");armor=ARMOR_UK.get(armor_type,armor_type);color=RARITY_UK.get(rarity,rarity)
        return " ".join(part for part in (slot,f"{item_level} рівня",armor,color) if part)
    return name if not name.startswith("Item ") else f"Предмет ID {item_id}"

def build_economy_equipment_report(events:list[Any],base_loot:list[dict[str,Any]],gold_from_mobs:float,final_gold:float)->dict[str,Any]:
    sales=[];final=[];daily={401:0,726:0};repair_cost=0.0;city_sale_gold=0.0
    for event in events:
        d=dict(getattr(event,"details",{}) or {});kind=str(getattr(event,"event_type",""))
        if kind=="daily_claim":daily[401]+=int(d.get("potions",0));daily[726]+=int(d.get("firius_tokens",0))
        if kind=="city_visit":sales.extend(d.get("sale_records",[]) or []);city_sale_gold+=float(d.get("sale_gold",0));repair_cost+=float(d.get("repair_cost",0))
        if kind=="simulation_final_state":final=list(d.get("inventory",[]) or [])
    found=defaultdict(int);meta={}
    for row in base_loot:
        key=int(row.get("item_id") or 0);found[key]+=int(row.get("found",0));meta[key]=dict(row)
    for key,qty in daily.items():
        if qty:found[key]+=qty;meta.setdefault(key,{"item_id":key,"name":STATIC_UK.get(key,str(key)),"category":"daily_reward","rarity":"common"})
    sold=defaultdict(int);sold_gold=defaultdict(float)
    for row in sales:sold[int(row.get("item_id") or 0)]+=int(row.get("quantity",0));sold_gold[int(row.get("item_id") or 0)]+=float(row.get("gold",0))
    remaining=defaultdict(int);equipped=defaultdict(int);final_loadout=[]
    for row in final:
        key=int(row.get("item_id") or 0);qty=int(row.get("quantity",0));dest=row.get("destination","remaining");(equipped if dest=="equipped" else remaining)[key]+=qty
        localized=item_name_uk(key,str(row.get("name","")),str(row.get("category","")),str(row.get("rarity","common")),str(row.get("slot_key","")),int(row.get("item_level",1)),str(row.get("armor_type","")))
        if dest=="equipped":final_loadout.append({**row,"name_uk":localized,"rarity_uk":RARITY_UK.get(str(row.get("rarity","")),str(row.get("rarity",""))),"slot_uk":SLOT_UK.get(str(row.get("slot_key","")),str(row.get("slot_key","")))})
    rows=[]
    for key in sorted(found):
        m=meta.get(key,{});used=max(0,found[key]-sold[key]-remaining[key]-equipped[key]);name_uk=item_name_uk(key,str(m.get("name","")),str(m.get("category","")),str(m.get("rarity","common")),str(m.get("slot_key","")),int(m.get("item_level",1)),str(m.get("armor_type","")))
        row={"item_id":key,"name_uk":name_uk,"name_raw":m.get("name"),"category":m.get("category"),"rarity":m.get("rarity"),"rarity_uk":RARITY_UK.get(str(m.get("rarity","")),m.get("rarity")),"found":found[key],"equipped":equipped[key],"sold":sold[key],"used_or_transformed":used,"remaining":remaining[key],"sale_gold":round(sold_gold[key],2)}
        if sum(row[x] for x in ("equipped","sold","used_or_transformed","remaining"))!=row["found"]:raise RuntimeError(f"Lifecycle conservation failed: {row}")
        rows.append(row)
    return {"loot_lifecycle":rows,"final_loadout":sorted(final_loadout,key=lambda x:str(x.get("slot_key"))),"gold":{"from_mobs":round(float(gold_from_mobs),2),"from_item_sales":round(city_sale_gold,2),"repair_cost":round(repair_cost,2),"final":round(float(final_gold),2)},"resources":{"refine_stones":{"found":found[601],"remaining":remaining[601]},"hp_potions":{"found":found[401]+found[402],"remaining":remaining[401]+remaining[402]},"runes":{"found":sum(q for k,q in found.items() if 701<=k<=725),"remaining":sum(q for k,q in remaining.items() if 701<=k<=725)}}}
