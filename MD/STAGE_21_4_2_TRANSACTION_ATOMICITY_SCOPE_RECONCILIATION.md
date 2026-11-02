# Stage 21.4.2 — Transaction atomicity scope reconciliation

- Status: **PASS_READ_ONLY**
- Parent: `8437b9859bae7c3b5496fc433868355aad577709`
- Prior static candidates: `34`
- Confirmed mutation cohort: `27`
- Delegated/caller-owned candidates: `7`
- Runtime-test-only unresolved: `0`
- Production mutations: **NONE**
- SQLite/WAL/SHM mutations: **NONE**
- Manual game check: **NOT REQUIRED**

## Classification summary

- **CALLER_OWNED_TRANSACTION**: 1
- **CONFIRMED_BOUNDARY_GAP**: 2
- **CONFIRMED_ROLLBACK_GAP**: 25
- **DELEGATED_TRANSACTION_HELPER**: 6

## Confirmed mutation cohort

- `db_modules/dev_compat.py::set_player_level_for_test:120` — CONFIRMED_ROLLBACK_GAP
- `db_modules/dev_compat.py::set_gold_for_test:207` — CONFIRMED_ROLLBACK_GAP
- `db_modules/dev_compat.py::seed_class_reset_sphere_item:735` — CONFIRMED_ROLLBACK_GAP
- `db_modules/dev_compat.py::create_dev_armor_item_for_test:1194` — CONFIRMED_ROLLBACK_GAP
- `db_modules/dev_compat.py::create_dev_weapon_item_for_test:1367` — CONFIRMED_ROLLBACK_GAP
- `db_modules/generated_equipment.py::create_generated_equipment_item:1006` — CONFIRMED_ROLLBACK_GAP
- `db_modules/inventory.py::consume_inventory_item:270` — CONFIRMED_ROLLBACK_GAP
- `db_modules/inventory.py::consume_user_item_by_item_id:352` — CONFIRMED_ROLLBACK_GAP
- `db_modules/inventory_compat.py::seed_class_reset_sphere_item:215` — CONFIRMED_ROLLBACK_GAP
- `db_modules/refine.py::init_refine_system:20` — CONFIRMED_ROLLBACK_GAP
- `db_modules/refine.py::set_inventory_refine_level:116` — CONFIRMED_ROLLBACK_GAP
- `db_modules/refine.py::ensure_refine_material_stack_sizes:245` — CONFIRMED_ROLLBACK_GAP
- `db_modules/shop.py::create_common_equipment_shop_preview:190` — CONFIRMED_ROLLBACK_GAP
- `systems/admin_crystal_credit_system.py::preview_admin_adjustment:18` — CONFIRMED_ROLLBACK_GAP
- `systems/auction_house_system.py::create_auction_lot_record:395` — CONFIRMED_ROLLBACK_GAP
- `systems/crystal_shop_system.py::_stack:32` — CONFIRMED_BOUNDARY_GAP
- `systems/equipment_system.py::apply_random_durability_wear_on_victory:3411` — CONFIRMED_ROLLBACK_GAP
- `systems/guild_system.py::cancel_guild_application:1157` — CONFIRMED_ROLLBACK_GAP
- `systems/guild_system.py::make_existing_guild_icons_unique:1288` — CONFIRMED_ROLLBACK_GAP
- `systems/guild_system.py::accept_guild_application:1422` — CONFIRMED_ROLLBACK_GAP
- `systems/guild_system.py::reject_guild_application:1528` — CONFIRMED_ROLLBACK_GAP
- `systems/guild_system.py::_guild_safe_set_application_status:1916` — CONFIRMED_ROLLBACK_GAP
- `systems/guild_system.py::accept_guild_application:1987` — CONFIRMED_ROLLBACK_GAP
- `systems/guild_system.py::recalculate_guild_level:2222` — CONFIRMED_ROLLBACK_GAP
- `systems/player_system.py::add_gold:1273` — CONFIRMED_ROLLBACK_GAP
- `systems/potion_system.py::use_potion_from_inventory:525` — CONFIRMED_ROLLBACK_GAP
- `systems/refine_system.py::consume:172` — CONFIRMED_BOUNDARY_GAP

## Safety decision

`GO_TO_21_4_3_TRANSACTION_ATOMICITY_IMPLEMENTATION`

Helper functions with caller-owned connections must not receive independent commits. Each confirmed owner-level fix requires an injected-failure test proving rollback and unchanged persistent state.
