# Stage 18.30.5

Simulation-only player-like resource lifecycle validation and restoration.

Rules fixed for this stage:

- HP potion is used before a hunt when current HP is below 40% and a potion exists.
- There is no combat escape policy. Once combat starts, it continues to victory or death.
- If HP is 25% or lower before a hunt, the character does not hunt and waits five minutes for canonical passive regeneration.
- Class-compatible runes are inserted after equipment resolution when slots and runes are available.
- Available refine stones are used against the best equipped item through the existing simulation refinement policy.
- Repair maintenance triggers at durability 15 or lower and continues to use the canonical production repair cost rule.
- Reported progression duration counts only active time inside the daily 09:00-23:00 window, while the canonical event timeline keeps absolute simulation minutes.

Only `systems/simulation` and simulation reporting/tests are changed. Production gameplay code and database files remain read-only.
