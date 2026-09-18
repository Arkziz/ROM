# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
policy = (ROOT / "MD" / "STAGE_18_29_1B_TEST_EVENT_AND_ARCHIVE_POLICY.md").read_text(encoding="utf-8")
readme = (ROOT / "events" / "README.md").read_text(encoding="utf-8")
namespace = (ROOT / "events" / "item_namespace.py").read_text(encoding="utf-8")
assert policy.count("ROM_STAGE_18_29_1B_TEST_EVENT_AND_ARCHIVE_POLICY") == 1
assert readme.count("ROM_STAGE_18_29_1B_TEST_EVENT_AND_ARCHIVE_POLICY") == 1
required_policy = (
    "test_event_2026", "🧪 Тестовий івент", "Europe/Kyiv",
    "`START_LOCAL`: `PENDING`", "`END_LOCAL`: `PENDING`",
    "test_slime", "🧪 Нестабільний слизень", "25%",
    "test_token", "ID `4000`", "test_reward", "ID `4001`",
    "test_reward_exchange", "operation_kind", "reward_kind",
    "Top size: `100`", "Page size: `10`", "Archive page size: `5`",
    "Status order: `active`, `upcoming`, `completed`", "ARCHIVE_VISIBLE",
    "generated_equipment_purchase", "multi-ingredient `recipe`",
)
for marker in required_policy:
    assert marker in policy, marker
required_readme = (
    "test_event_2026", "Europe/Kyiv", "4000..4024",
    "по 5 на сторінці", "active, upcoming, completed", "top-100", "по 10 позицій",
)
for marker in required_readme:
    assert marker in readme, marker

tree = ast.parse(namespace)
values = {}
for node in tree.body:
    target = value = None
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        target, value = node.targets[0].id, node.value
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        target, value = node.target.id, node.value
    if target:
        try:
            values[target] = ast.literal_eval(value)
        except Exception:
            pass
assert values["EVENT_STATIC_ITEM_MIN"] == 4000
assert values["EVENT_STATIC_ITEM_MAX"] == 9999
assert values["EVENT_ITEM_BLOCK_SIZE"] == 25
assert values["EVENT_ITEM_BLOCK_COUNT"] == 240
assert values["EVENT_ITEM_BLOCKS"] == {}
print("TEST_EVENT_AND_ARCHIVE_POLICY_18_29_1B_OK")
