# Stage 18.30.3a

Integrates encounter type and battle outcome into progression events, records per-item victory loot, adds time-to-target details, and writes full JSON/CSV reports to `reports/simulation`. Console output is compact. Loot conservation is blocking.

Manual check: run `python .\tools\run_class_progression_simulation.py --class scout --target-level 2 --seed 1` and review the concise summary and both report paths.
