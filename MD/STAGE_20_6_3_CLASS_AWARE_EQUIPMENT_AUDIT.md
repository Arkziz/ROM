# Stage 20.6.3 — Class-aware Equipment Generation Audit

**STRICT_WEIGHTED_OPTIONS_AND_ROOT_CAUSE_READY**

## Exact root cause

- Shop preview is always target-class weighted and purchase promotes the same snapshot.
- Loot first rolls `is_class_aware`; only that branch redistributes primary stats.
- The unrestricted branch can produce off-class primary stats.
- DEV omits `class_aware_chance`, so it defaults to unrestricted.

## Rogue amulet WIS

Canonical Rogue jewelry allows only `DEX / STR / STA`. WIS is therefore not a result of the canonical weighted Rogue jewelry profile. WIS can occur through the unrestricted branch and is a bug only if Stage 20.6.4 chooses STRICT policy.

## Policy decision

### STRICT
All generated equipment for a player is always redistributed by target class and slot policy.

### WEIGHTED
Keep current class-aware probability; non-class-aware branch remains unrestricted.

Production code and DB were unchanged. Manual verification is not required before the policy decision.
