# -*- coding: utf-8 -*-
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import events
from events import item_namespace as ns
module = importlib.import_module("events.test_event_2026")

assert module.EVENT_KEY == "test_event_2026"
assert module.EVENT_NAME == "🧪 Тестовий івент"
assert module.ENABLED is False
assert module.ARCHIVE_VISIBLE is True
assert module.EVER_LAUNCHED is False
assert module.TIMEZONE_NAME == "Europe/Kyiv"
assert module.START_LOCAL is None and module.END_LOCAL is None
assert module.DATE_POLICY == "PENDING_KYIV_ACTIVATION"
assert module.START_AT.tzinfo is not None and module.END_AT.tzinfo is not None
assert module.START_AT < module.END_AT
assert ns.EVENT_ITEM_BLOCKS == {"test_event_2026": ((4000, 4024),)}
items = module.get_item_definitions()
assert isinstance(items, tuple) and len(items) == 2
assert [item["id"] for item in items] == [4000, 4001]
assert ns.validate_event_item_definitions(items) == items
mobs = module.get_mob_candidates(None)
assert len(mobs) == 1 and mobs[0]["mob_key"] == "test_slime"
assert mobs[0]["chance_percent"] == 25.0
assert mobs[0]["all_huntable_locations"] is True
assert mobs[0]["mob_template"]["attack_type"] == "physical"
drops = module.get_drop_rules(None)
assert len(drops) == 1 and drops[0]["item_id"] == 4000
assert drops[0]["quantity"] == 1 and drops[0]["chance_percent"] == 100.0
offers = module.get_shop_offers()
assert len(offers) == 1
assert offers[0]["operation_kind"] == "exchange"
assert offers[0]["reward_kind"] == "static_item"
assert offers[0]["cost_item_id"] == 4000 and offers[0]["cost_quantity"] == 3
assert offers[0]["reward_item_id"] == 4001 and offers[0]["reward_quantity"] == 1
stats = module.get_statistics_definitions()
assert len(stats) == 1 and stats[0]["top_size"] == 100 and stats[0]["page_size"] == 10
assert module.get_boss_candidates(None) == ()
assert module.register_handlers(object()) == ()
assert "events.test_event_2026" in events.EVENT_MODULES
assert tuple(events.get_active_events()) == ()
print("TEST_EVENT_CONTENT_PACKAGE_18_29_2_OK")
