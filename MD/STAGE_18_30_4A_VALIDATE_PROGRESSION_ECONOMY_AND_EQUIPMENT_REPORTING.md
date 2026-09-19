# Stage 18.30.4a

Fixes the short-run equipment lifecycle found during manual validation. Better equipment is equipped immediately; rejected and replaced equipment is sold immediately. Loot metadata now preserves slot, armor type, item level and stats, producing Ukrainian-readable names such as `Шолом 1 рівня шкіра білий`.

The runner creates exactly three transferable files: full JSON, localized loot CSV, and equipment JSON.

Manual check: run Scout 1 to 2 and confirm non-zero equipped and sold counts, non-empty equipment JSON, readable Ukrainian equipment names, and exactly three report paths.
