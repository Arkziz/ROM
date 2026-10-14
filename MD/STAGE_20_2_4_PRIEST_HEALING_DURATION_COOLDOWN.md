# Stage 20.2.4 — аудит тривалості та cooldown лікування Жерця

- Статус: **PASS**
- Рішення: **CONDITIONAL_GO**

## Canonical skill definition

- Cost: `30 MP`
- Declared cooldown: `3`
- Description duration: `4 turns`
- Effect: `player_hot`

## Lifecycle evidence

- `definition`: 5 evidence points
- `hot`: 10 evidence points
- `cooldown`: 32 evidence points
- `duration`: 18 evidence points
- `presentation`: 8 evidence points

## Findings

### COOLDOWN_PLUS_ONE_RUNTIME_SEMANTICS
- Severity: **HIGH**
- PvE stores cooldown_turns + 1 and decrements at player-turn start; the effective availability window must be proven against the displayed 3-turn contract.
- Next stage: `20.2.5`

### DURATION_LITERAL_DISTRIBUTION
- Severity: **HIGH**
- The 4-turn HoT duration is repeated across skill text, PvE application, PvP fallback and simulator effect creation instead of one lifecycle policy owner.
- Next stage: `20.2.5`

### FIRST_FINAL_TICK_PARITY
- Severity: **HIGH**
- PvE, PvP and simulator tick/decrement ordering differs by implementation shape; exact first tick, fourth tick, expiry and victory rollback require executable parity tests.
- Next stage: `20.2.5`

### REAPPLICATION_POLICY_REPLACE
- Severity: **MEDIUM**
- Current effect dictionaries imply replacement/refresh under the same key; the intended reapplication policy must be made explicit and tested.
- Next stage: `20.2.5`

## Audit decision

**CONDITIONAL_GO**

Owners and current lifecycle are mapped with no blocking corruption. Stage 20.2.5 may consolidate duration/cooldown policy and add cross-engine executable lifecycle tests.

## Manual verification

**Не потрібна.** Це read-only audit.

