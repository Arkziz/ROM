# ROM Stage 18.29.4b: Test Event Drop Integration

The canonical victory reward route now calls the existing event-drop adapter after ordinary enemy drops.

- Event source: registered event drop rules.
- Pilot rule: `test_event_2026:test_token`.
- Eligible mob: `test_event_2026:test_slime`.
- Reward: item `4000`, quantity 1, probability 100 percent.
- Award owner: canonical inventory `add_item` adapter already used by `process_event_drops`.
- Ordinary mobs without event metadata receive no event drop.
- The event-drop result is exposed separately in the victory reward contract.
- Event runtime remains disabled pending Kyiv activation dates.
- Telegram UI and activation dates are not changed.
