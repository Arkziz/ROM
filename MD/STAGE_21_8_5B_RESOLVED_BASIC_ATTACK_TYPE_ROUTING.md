# Stage 21.8.5b - Resolved basic attack type routing

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contract: **BASIC_ATTACK_TYPE_ROUTING**
- V1 owner: `systems/stat_system.py`
- Function: `resolve_basic_attack_type`
- Allowed routing results: `physical`, `magical`
- Unresolved rows: **0**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Binding decision

The unique V1 function `resolve_basic_attack_type` is the authoritative owner of basic-attack damage-type selection. Stage 21.8.5 implementation must preserve that routing as a typed policy and must not derive attack type from resource cost, UI text, or DTO presentation fields.

## Scope

This patch resolves documentation and contract evidence only. It does not modify V1, V2 production code, persistence, Telegram handlers, or runtime databases.
