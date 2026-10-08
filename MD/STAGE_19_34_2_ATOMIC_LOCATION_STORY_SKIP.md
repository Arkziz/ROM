# Stage 19.34.2: атомарний overlevel SKIP

При перевищенні canonical `level_max` усі незавершені production-квести попередньої локації атомарно матеріалізуються як `SKIPPED` без нагород. `COMPLETED` зберігаються, isolated quest items очищуються, повторний виклик idempotent, а гравець отримує одне summary-повідомлення. Межі беруться з `LOCATIONS`; WAL/SHM не маніпулювалися. Manual verification: REQUIRED.
