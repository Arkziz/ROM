# Stage 18.30.6

Enables the existing six-class matrix runner for target level 10 while preserving the already accepted target level 2 route. The same canonical progression engine, class order, seed, profile, time reporting, validation, and two aggregate outputs are used. The runner accepts only target levels 2 and 10. Gameplay, RNG, single-class reporting, database, WAL, and SHM are unchanged.

Night command: `python .\tools\run_all_class_progression_matrix.py --target-level 10 --seed 3`.
