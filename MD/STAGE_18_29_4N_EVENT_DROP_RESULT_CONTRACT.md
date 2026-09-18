# ROM Stage 18.29.4n: Event Drop Result Contract

The victory formatter now consumes the actual `process_event_drops()` shape: `payload` plus nested canonical `add_item()` `result`. It renders only `result.success=True` with positive `result.added`, using `result.name` and the actual added quantity. No inventory mutation occurs in presentation.
