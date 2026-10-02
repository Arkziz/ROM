# Stage 19.27.12: story-boss player context adapter

Виправлено runtime traceback під час «Оглянутися»: canonical `get_player_stats()` повертає tuple первинних характеристик і більше не перетворюється через `dict(...)`. Поточна локація читається через `db.get_current_location`. Стан, коли квест 49 доступний, але ще не прийнятий, повертає відсутність story-boss presentation без traceback. Ручна перевірка обов’язкова.
