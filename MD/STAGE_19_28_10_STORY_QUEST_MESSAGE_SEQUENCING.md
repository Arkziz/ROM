# Stage 19.28.10: message sequencing сюжетних квестів

ACCEPT now emits one ACTIVE card with an inline success marker instead of a generic receipt plus duplicate card. COMPLETE always emits the canonical receipt, then refreshes the current NPC only when that presentation contains a meaningful quest. Same-NPC continuation remains two messages; cross-NPC handoffs and quest 50 no longer append an empty NPC card. Lifecycle, rewards, ownership, callbacks and database are unchanged.
