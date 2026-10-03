# Stage 19.28.2: state-aware navigation сюжетних квестів

Production journal now resolves routes from lifecycle state, quest type, progress and authoritative NPC ownership. AVAILABLE points to the giver; incomplete combat/item objectives point to `Початок Шляху`; BOSS points to `Роззирнутися`; ready objectives point to the completion NPC; terminal states show no active route. Quest 23 now routes to the Trader through `turn_in_npc_id`. Definitions and database are unchanged.
