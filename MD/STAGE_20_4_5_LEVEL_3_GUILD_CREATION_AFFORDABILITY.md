# Stage 20.4.5 — Level-3 Guild Creation Affordability

## Decision
`REDUCE_GUILD_COST_TO_50`. Recommended creation cost: `50.00` gold.

The audit ran six classes with one deterministic seed each to reached level 3. Effective wallet adds canonical story gold `7.00` and level-up gold `1.88` to the simulator net wallet. Candidates `100/75/50` are compared by affordability and additional level-3 normal-mob grind at `0.215` expected gold per kill.

## Candidate summary
- 100: typical classes affording `0/6`; typical median extra kills `395.0`.
- 75: typical classes affording `0/6`; typical median extra kills `279.0`.
- 50: typical classes affording `0/6`; typical median extra kills `162.5`.

Selection rule: highest tested cost with typical median additional grind no more than 100 level-3 normal kills; otherwise 50. Production code is unchanged.
