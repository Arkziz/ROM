# Stage 22.2.3 import, direct attribute, wrapper and late-binding call path

- Status: **PASS_READ_ONLY**
- Patch revision: **1**
- Parent: `79f0a9340ca227cd5c95c60d20eaa8a0a3891504`
- Python files: **1038**
- Static call sites: **55754**
- Direct-name calls: **31862**
- Attribute calls: **23830**
- Dynamic/late-binding sites: **456**
- Wrapper candidates: **1624**
- Telegram registrations linked: **375**
- Deletion authorized: **false**
- Production mutations: **NONE**
- Production SQLite opened: **false**

## Scope
The audit resolves static import aliases, direct calls, module attributes, effective local definitions, small delegation wrappers and dynamic-binding sites. Runtime reachability is not claimed where source-only evidence is insufficient.

## Decision
`GO_TO_22_2_4_ROUTE_OVERLAP_SHADOW_DUPLICATE_RESPONSE_AND_DEAD_PATH_CLASSIFICATION`
