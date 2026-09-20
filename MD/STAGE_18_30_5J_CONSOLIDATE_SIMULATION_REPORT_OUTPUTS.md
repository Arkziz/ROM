# Stage 18.30.5j

The class progression runner now creates exactly two report files per run: the authoritative full JSON and the consolidated XLSX workbook.

The superseded `_loot.csv` and `_equipment.json` outputs are no longer created. Their information remains available in the main JSON and in the `Loot Lifecycle` and `Final Equipment` workbook sheets. Existing report files from older runs are not deleted or modified.

This reporting-only recovery does not change simulation logic, RNG, battles, loot, equipment decisions, refinement, runes, durability, economy, or database state.
