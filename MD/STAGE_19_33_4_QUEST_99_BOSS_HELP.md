# Stage 19.33.4: help-паритет boss-квесту 99

Story card квесту 99 у Голови Найманців тепер має inline-кнопку «🧭 Як знайти Короля Гоблінів». Adapter і callback wiring узагальнено для production BOSS-квестів 49 і 99; callback прив’язаний до фактичного номера active quest. Combat owner, progress, rewards, DB та WAL/SHM не змінювалися. Manual verification: REQUIRED.
