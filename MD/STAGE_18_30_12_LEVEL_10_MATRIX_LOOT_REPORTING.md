# Stage 18.30.12

Restores the all-class level 1 to 10 matrix and expands loot reporting. Failed two-item simulator daily rewards are atomic, preventing repeated Firius Token grants. The class progression payload exports detailed and grouped equipment data. XLSX adds Loot Details, Equipment Summary, and Equipment Details. Production gameplay owners, database, WAL and SHM are unchanged.

Run: `python .\tools\run_all_class_progression_matrix.py --target-level 10 --seed 3 --max-days 365`.
