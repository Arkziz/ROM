# Stage 22.1.7 - get_dynamic_sell_price Focused Runtime Evidence

- Status: **PASS_READ_ONLY**
- Parent: `49e42a98cfc3f78917daa008d6fc4cbba036bd3a`
- Symbol: **get_dynamic_sell_price**
- Runtime canonical module: **db_modules.generated_equipment**
- Runtime canonical file: **db_modules/generated_equipment.py**
- Parity samples: **4/4 PASS**
- Owner decisions deferred: **0**
- Deletion authorized: **NO**
- Decision: **GO_TO_22_1_8_DOMAIN_OWNER_MAP**
- Production mutations: **NONE**
- DB/WAL/SHM mutations: **NONE**
- Manual game check: **NOT_REQUIRED**

The focused runtime probe proves the module returned by `systems.dynamic_equipment_system._canonical()`, validates callable/module identity, verifies the production caller in `db_modules/shop.py`, executes the maintained focused smoke test, and compares representative outputs across dynamic, canonical, dev-compat, and generated entrypoints. No deletion or production mutation is authorized.
