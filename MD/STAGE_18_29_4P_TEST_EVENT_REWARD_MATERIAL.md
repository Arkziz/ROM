# ROM Stage 18.29.4p: Test Event Reward as Material

The pilot reward `🎁 Пам’ятний знак випробування` (`items.id=4001`) is reclassified from `collectible` to the existing canonical `material` inventory category. Its type, rarity, stack limit, binding and trade restrictions remain unchanged. Existing inventory rows require no migration because category is owned by the item catalog row. A dedicated collections section is intentionally deferred until a future real use case exists.
