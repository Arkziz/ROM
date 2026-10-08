# Stage 19.36.3: acceptance розширеного журналу сюжетних квестів

Acceptance decision: **ACCEPTED**.

## Прийнято

- Дві історії, 10 розділів і 100 квестів у canonical порядку.
- Status icons: ✅ completed, 📖 active, ✨ available, 🔒 locked, ⏭️ skipped.
- Finalized `COMPLETED + SKIPPED` розділ показується через ⏭️, а progress рахує лише completed.
- Root-кнопка `🔙 До профілю` використовує canonical `story_quest:profile` і `send_profile_root`.
- Навігація Історія → Розділ → Квест → Назад прийнята вручну без помилок.
- Пагінація не потрібна, доки canonical розділ містить 10 квестів.

Stage 19.36 закрито. Наступний етап: Stage 19.37 full regression і closure audit.
