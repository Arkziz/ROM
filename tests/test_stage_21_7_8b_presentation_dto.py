from rom_v2.presentation.item_dto import *
def source(i=11,refine=2):
 return ItemPresentationInput(7,i,"Клинок",category="equipment",slot_key="main_hand",rarity="rare",item_level=5,required_level=5,durability=80,refine_level=refine,primary_stats={"sta":2,"str":5,"zero":0},defenses={"mdef":1,"pdef":3},damage={"physical_max":12,"physical_min":8},runes=(RunePresentation(1,22,"B"),RunePresentation(0,21,"A")))
def test_description_is_typed_and_deterministic():
 dto=build_item_description(source());assert dto.inventory_id==11 and dto.display_name=="Клинок +2";assert [x.key for x in dto.fields]==["category","slot_key","rarity","item_level","required_level","durability","refine_level","str","sta","pdef","mdef","physical_min","physical_max"];assert [x.socket_index for x in dto.runes]==[0,1]
def test_identity_is_not_display_text():
 a=build_item_description(source(11));b=build_item_description(source(12));assert a.display_name==b.display_name and a.inventory_id!=b.inventory_id
def test_comparison_uses_exact_instances_and_stable_keys():
 a=build_item_description(source(11,3));b=build_item_description(source(12,1));c=compare_items(a,b);assert (c.selected_inventory_id,c.equipped_inventory_id)==(11,12);assert next(x for x in c.rows if x.key=="refine_level").relation==1
def test_optional_fields_and_validation():
 dto=build_item_description(ItemPresentationInput(1,None,"Річ"));assert all(x.key!="durability" for x in dto.fields)
 try:compare_items(dto,dto)
 except ValueError as e:assert str(e)=="comparison_requires_owned_instances"
 else:raise AssertionError("comparison must require inventory ids")
