# Stage 18.30.9

Adds a separate fixed 10-day diagnostic matrix for all six classes. It deliberately uses an unreachable diagnostic target level and accepts `max_days_reached` as success, so every class is reported after exactly 10 days even when level 5 is not reached. Outputs include class summaries, daily combat/EXP/daily-reward/repair diagnostics, final equipment durability, and lifecycle validation. Existing progression matrix modes and gameplay are unchanged.

Command: `python .\tools\run_all_class_10_day_diagnostic_matrix.py --days 10 --seed 3`.
