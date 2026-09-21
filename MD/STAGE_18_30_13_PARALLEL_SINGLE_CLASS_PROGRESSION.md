# Stage 18.30.13

Adds a parallel-safe runner for one selected class and one selected target level from 2 through 10. Six independent terminals may run six different classes concurrently. Each process owns unique JSON/XLSX paths under `reports/simulation/single_class`, so reports do not overwrite each other. The runner never writes `game.db`, WAL or SHM. It preserves detailed loot, equipment summary/details, final equipment and validation. A max-days result is saved as PARTIAL instead of losing the completed simulation.
