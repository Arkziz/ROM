# Stage 19.34.2a: відновлення повідомлення про рівень

Після бойового level-up повідомлення про новий рівень завжди надсилається перед summary overlevel SKIP. Якщо canonical milestone message порожній, fallback показує перехід рівня та `+5` вільних очок за кожний отриманий рівень. Спеціальні canonical reward messages не дублюються. SKIP, EXP, HP, rewards, DB і WAL/SHM не змінювалися. Manual verification: REQUIRED.
