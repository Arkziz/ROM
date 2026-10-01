# Stage 19.26.6: Fix itemless TURN_IN runtime scope

The `_turn_in_text(presentation)` helper now reads `definition.required_quest_items`, matching its local binding. The itemless quest 40 remains ACTIVE and the database is untouched.
