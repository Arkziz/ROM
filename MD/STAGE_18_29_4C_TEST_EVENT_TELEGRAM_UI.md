# ROM Stage 18.29.4c: Test Event Telegram UI

Adds `🎉 Івенти` to the existing account Menu. The event screen uses a dedicated callback namespace `evt:test_event_2026:*`, so its `🏆 Рейтинг` inline button cannot collide with the existing reply-keyboard player ranking.

The UI includes event information, top-100 ranking with 10 rows per page, guild names in square brackets, own position, refresh and navigation, a shop with one exchange per action and explicit confirmation, and inactive-state blocking. The archive is intentionally deferred to a separate stage because it is a cross-event navigation system. The pilot event remains disabled pending Kyiv dates.
