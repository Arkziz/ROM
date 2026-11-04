# Stage 21.8.1 - Monolith Reduction Scope Audit

- Status: **PASS_READ_ONLY**
- Parent: `96b2fe93fcbd966add57a3d652b27fbb2f70e2a6`
- Targets: **handlers/combat.py, handlers/dev.py**
- Extraction candidates: **15**
- Findings: **9**
- High findings: **1**
- Blocking findings: **0**
- Decision: **RECONCILE_21_8_2_MONOLITH_OWNER_CALL_PATH_AND_EXTRACTION_SLICES**
- Production mutations: **NONE**
- DB/WAL/SHM mutations: **NONE**
- Manual game check: **NOT_REQUIRED**

## Target summary
- `handlers/combat.py`: 3906 lines, 53 functions, 5 large, 1 very large, 11 extraction candidates
- `handlers/dev.py`: 1135 lines, 11 functions, 1 large, 1 very large, 4 extraction candidates

## Findings
- REVIEW: `VERY_LARGE_FUNCTION_OWNER` in `handlers/combat.py` (1)
- REVIEW: `PRESENTATION_DOMAIN_MIX` in `handlers/combat.py` (4)
- REVIEW: `DB_PRESENTATION_MIX` in `handlers/combat.py` (1)
- REVIEW: `MUTABLE_MODULE_GLOBALS` in `handlers/combat.py` (3)
- HIGH: `DUPLICATE_TOP_LEVEL_OWNER` in `handlers/dev.py` (1)
- REVIEW: `VERY_LARGE_FUNCTION_OWNER` in `handlers/dev.py` (1)
- REVIEW: `PRESENTATION_DOMAIN_MIX` in `handlers/dev.py` (1)
- REVIEW: `MUTABLE_MODULE_GLOBALS` in `handlers/dev.py` (1)
- REVIEW: `NO_DIRECT_TEST_TOOL_REFERENCES` in `handlers/dev.py` (1)

## Required successor

Stage 21.8.2 must convert candidates into exact owner/call-path slices and select the shortest behavior-preserving extraction scope before any production mutation.
