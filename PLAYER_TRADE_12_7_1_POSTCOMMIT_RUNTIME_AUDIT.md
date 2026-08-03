# Player Trade 12.7.1 Post-Commit Runtime Audit

- Generated: `2026-08-03T21:14:28+00:00`
- Verdict: **PASS**
- Mode: **read-only**
- Gameplay mutations: **0**
- Database writes: **0**
- Database files unchanged: **YES**

## Runtime Database Integrity

- `PRAGMA quick_check`: `['ok']`
- Foreign-key issues: `0`
- Active trades: `0`
- Trade rows: `31`
- Offer rows: `42`
- Event rows: `193`
- History rows: `31`

### Trade Status Counts

- `cancelled`: `21`
- `completed`: `4`
- `expired`: `6`

### Integrity Checks

- `orphan_trade_reservations`: `0`
- `terminal_trade_reservations`: `0`
- `orphan_trade_sessions`: `0`
- `terminal_trade_sessions`: `0`
- `completed_without_history`: `0`
- `terminal_without_history`: `0`
- `history_without_trade`: `0`
- `history_status_mismatch`: `0`
- `duplicate_history_trade_ids`: `0`
- `completed_without_completed_event`: `0`
- `duplicate_completed_events`: `0`
- `offer_wrong_owner`: `0`
- `active_offer_missing_inventory`: `0`
- `active_offer_owner_mismatch`: `0`
- `active_offer_quantity_exceeds_inventory`: `0`
- `confirming_not_both_ready`: `0`
- `editing_with_final_confirm`: `0`

## Static Architecture and Commit Contracts

- `actor_only_ready_reset`: **OK**
- `both_final_confirms_reset_on_mutation`: **OK**
- `unlock_preserves_other_ready`: **OK**
- `begin_immediate`: **OK**
- `committing_transition`: **OK**
- `completed_transition`: **OK**
- `reservation_revalidation`: **OK**
- `gold_validation`: **OK**
- `bag_capacity_validation`: **OK**
- `history_write`: **OK**
- `event_write`: **OK**
- `session_cleanup`: **OK**
- `reservation_cleanup`: **OK**
- `idempotent_completed`: **OK**
- `first_ready_local`: **OK**
- `both_ready_final_sync`: **OK**
- `final_refresh_callback`: **OK**
- `confirmation_whitelisted`: **OK**
- `simple_completion_text`: **OK**
- `technical_completion_text_absent`: **OK**

## Findings

No findings.

## Conclusion

The audit inspected the live SQLite database in query-only mode and parsed/compiled the current Player Trade source files without importing `main.py` or running cleanup.
