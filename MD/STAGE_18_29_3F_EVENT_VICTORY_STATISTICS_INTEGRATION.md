# ROM Stage 18.29.3f: Event Victory Statistics Integration

The canonical `handlers.combat.process_victory()` route now records an event-mob victory only after `claim_pve_terminal(user_id, "victory", encounter_id)` succeeds.

- Identity: existing persistent `pve_encounters.encounter_id`.
- Event detection: non-empty `mob.event_key` and `mob.event_mob_key`.
- Ordinary mobs remain unchanged.
- Stale callbacks return before statistics.
- The receipt table provides a second exactly-once guard.
- Defeat, escape and unfinished combat do not call the statistics API.
- Event runtime remains disabled; no gameplay encounter can occur yet.
