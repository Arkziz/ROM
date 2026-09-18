# ROM Stage 18.29.4m: Event Drop Victory Text

The canonical victory formatter now reads already-awarded `event_drop_results` and renders successful event rewards in a separate `🎉 Івентна нагорода:` block. `🎒 Лут не знайдено.` is shown only when both ordinary loot and awarded event-drop messages are absent. The presentation layer remains read-only and never calls inventory mutation.
