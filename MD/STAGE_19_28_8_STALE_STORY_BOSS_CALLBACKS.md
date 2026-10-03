# Stage 19.28.8: stale story-boss callbacks

Old HELP, RETURN and INVOKE payloads now pass one authoritative active-quest gate before action branching. AVAILABLE, COMPLETED, SKIPPED, wrong-quest and missing-call states return only a neutral alert. ACTIVE 0/1 keeps HELP/RETURN/INVOKE behavior; ACTIVE 1/1 keeps report HELP/RETURN but INVOKE remains denied by the existing presentation gate. Combat and boss lifecycle are unchanged.
