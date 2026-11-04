# Stage 22.1.7a - Correct Rarity Runtime Evidence

- Status: **PASS_READ_ONLY**
- Parent: `61e52eb058af9da077ff534b1b94334329282e59`
- Symbol: **get_dynamic_sell_price**
- Runtime canonical module: **db_modules.generated_equipment**
- Runtime canonical file: **db_modules/generated_equipment.py**
- Production rarity keys: **common, uncommon, rare, epic**
- Corrected rarity parity: **4/4 PASS**
- Invalid-rarity fallback: **PASS**
- Prior uppercase/LEGENDARY fixtures: **INVALID_TEST_INPUT**
- Owner decisions deferred: **0**
- Deletion authorized: **NO**
- Decision: **GO_TO_22_1_8_DOMAIN_OWNER_MAP**
- Production mutations: **NONE**
- DB/WAL/SHM mutations: **NONE**
- Manual game check: **NOT_REQUIRED**

The corrective runtime probe reads the actual production rarity keys, marks the previous uppercase/LEGENDARY matrix as invalid test input, proves the module returned by `systems.dynamic_equipment_system._canonical()`, validates callable/module identity, verifies the production caller in `db_modules/shop.py`, executes the maintained focused smoke test, and compares representative outputs across dynamic, canonical, dev-compat, and generated entrypoints. No deletion or production mutation is authorized.
