# Stage 18.30.5e

Simulation-only restoration of canonical refinement lifecycle.

`SimulationMetaProgressionService.refine_best()` now delegates refine kind, maximum level, success chance, and failure level to `systems.refine_system`. It allows attempts only when the canonical next-attempt chance is at least 50%, blocks lower chances without consuming a stone or calling RNG, ignores broken and non-refinable equipment, and consumes all available stones while an eligible target remains.

Target selection is deterministic: higher item level, then canonical rarity rank, then simulation item ID. Production gameplay code and database files remain unchanged.

Stage 18.30.5d's dynamic fixtures accidentally constructed the stone with reversed identifiers, so their stone quantity was zero. The static findings about duplicated tables, missing canonical owner, and missing 50% gate remain valid; this patch's smoke test corrects the fixture and validates the actual mutation path.
