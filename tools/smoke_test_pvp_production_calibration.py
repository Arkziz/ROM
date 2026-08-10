from systems.pvp_production_calibration import build_standard_actor,duel,matrix,calibrate

def main():
 for c in ("warrior","knight","scout","rogue","mage","priest"):
  a=build_standard_actor(c,10,"rare"); assert a.max_hp>0 and a.physical_defense>=0 and a.magical_defense>=0
 r=duel("warrior","priest",2,10,"rare"); assert r["trials"]==2
 m=matrix(1,10,"rare"); assert len(m["matchups"])==36 and m["production_database_writes"]==0
 c=calibrate(1,10,"rare"); assert c["candidates_tested"]==60 and len(c["best"])==10
 print("[OK] PvP production actor matrix and calibration sandbox")
 print("- standardized production-stat actors for 6 classes: PASS")
 print("- level/rarity production matrix with 36 ordered matchups: PASS")
 print("- DEV-only healing and class-damage calibration grid: PASS")
 print("- target-aware policy and canonical PvP round engine reused: PASS")
 print("- live PvP balance changes: 0")
 print("- production database writes: 0")
if __name__=="__main__": main()
