# Stage 18.30.13a

Fixes report generation for every single-class run. Each XLSX worksheet table is now created once after all rows are appended, eliminating duplicate table-name failures. JSON is atomically persisted and announced before XLSX generation, so a future Excel-only failure cannot hide or lose the completed simulation result. Already running Python processes retain the old loaded runner and should be restarted after this patch if they have not yet completed.
