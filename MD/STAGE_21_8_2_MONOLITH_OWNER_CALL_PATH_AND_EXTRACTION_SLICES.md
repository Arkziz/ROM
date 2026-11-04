# Stage 21.8.2 - Monolith Owner, Call Path and Extraction Slices

- Status: **PASS_READ_ONLY**
- Parent: `e8586a19a1397cc3faeffac31cad3c616464d0bf`
- Dev owner definitions: **4**
- Active dev owner line: **1058**
- Combat slices classified: **7**
- Recommended first slice: **`build_lethal_combat_log`**
- Target module: **`handlers/combat_formatting.py`**
- Blocking items: **0**
- Decision: **IMPLEMENT_21_8_3_COMBAT_LOG_FORMATTING_EXTRACTION**
- Production mutations: **NONE**
- DB/WAL/SHM mutations: **NONE**
- Manual game check: **NOT_REQUIRED**

## Safety decision

The four `register_dev_handlers` definitions form a historical wrapper chain. They are not deleted or collapsed in this stage. The first implementation slice is the smallest formatting owner with maintained smoke references, no DB transaction ownership, and no Telegram registration change.
