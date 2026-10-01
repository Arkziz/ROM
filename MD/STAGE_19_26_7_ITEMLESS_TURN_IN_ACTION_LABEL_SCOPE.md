# Stage 19.26.7: Fix itemless TURN_IN action-label scope

The `_turn_in_item_action_label(definition, active=False)` helper now reads its local `definition.required_quest_items` binding in both conditional branches. The checker executes the pure helper for itemless and item-backed cases.
