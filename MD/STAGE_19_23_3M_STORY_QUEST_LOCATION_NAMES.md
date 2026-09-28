# Stage 19.23.3m: Localized story-quest location names

Story quest UI now resolves player-facing location names through one canonical resolver. Technical IDs such as `start_path` and artificial text such as `Start Path` are forbidden. Unknown location IDs fail closed in automated validation. The policy applies to current and future story quests.
