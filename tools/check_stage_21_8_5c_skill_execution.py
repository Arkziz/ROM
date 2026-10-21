from rom_v2.domain.skill_execution import DamageType,SkillDefinition,SkillKind
assert DamageType.PHYSICAL.value=="PHYSICAL" and DamageType.MAGICAL.value=="MAGICAL"
assert SkillDefinition("basic",SkillKind.BASIC_ATTACK).cost==0
print("[PASS] Stage 21.8.5c skill execution API smoke check")
