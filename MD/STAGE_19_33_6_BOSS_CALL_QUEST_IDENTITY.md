# Stage 19.33.6: identity contract сюжетного boss-call

`get_active_story_boss_call()` тепер повертає authoritative `quest_number`, `quest_status`, `progress_current` і `progress_target`. Це усуває fallback до legacy квесту 49 та дозволяє `👀 Роззирнутися` правильно показувати Короля Гоблінів для active квесту 99. Eligibility, combat owner, progress, rewards, DB і WAL/SHM не змінювалися. Manual verification: REQUIRED.
