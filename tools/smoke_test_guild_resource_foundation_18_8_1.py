#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.guild_resource_policy import GUILD_RESOURCE_SINKS, GUILD_RESOURCE_SPENDING_ENABLED
from systems.guild_resource_system import (
    activate_guild_resource_sink,
    get_guild_resource_design_policy,
    get_guild_resource_sink_definition,
    spend_guild_resource,
)

assert GUILD_RESOURCE_SPENDING_ENABLED is False
assert len(GUILD_RESOURCE_SINKS) == 6
assert [sink["order"] for sink in GUILD_RESOURCE_SINKS] == [1, 2, 3, 4, 5, 6]
assert GUILD_RESOURCE_SINKS[0]["key"] == "member_limit"
assert all("price" not in sink for sink in GUILD_RESOURCE_SINKS)
assert get_guild_resource_sink_definition("member_limit")["status"] == "planned"
assert get_guild_resource_sink_definition("missing") is None
assert get_guild_resource_design_policy()["spending_enabled"] is False
assert spend_guild_resource()["success"] is False
assert activate_guild_resource_sink()["code"] == "guild_resource_spending_inactive"

system_source = (ROOT / "systems" / "guild_resource_system.py").read_text(encoding="utf-8-sig")
system_tree = ast.parse(system_source)
for forbidden in ("sqlite3", "cursor.execute", "UPDATE ", "INSERT ", "DELETE ", "CREATE TABLE"):
    assert forbidden not in system_source, forbidden
assert len([n for n in system_tree.body if isinstance(n, ast.FunctionDef) and n.name == "spend_guild_resource"]) == 1

handler_source = (ROOT / "handlers" / "guild.py").read_text(encoding="utf-8-sig")
for forbidden in ("• EXP:", "• Score:", "Score: {", " | EXP:", "Level progress:", " | Resource:", " | Kills:", " | Contracts:"):
    assert forbidden not in handler_source, forbidden
for required in ("• Досвід:", "• Бали:", "Бали: {", " | Досвід:", "Прогрес рівня:", " | Ресурс:", " | Вбивства:", " | Контракти:"):
    assert required in handler_source, required
assert "/guild_add_progress EXP RESOURCE KILLS CONTRACTS" in handler_source
print("PASS: Ukrainian guild labels and inactive no-write guild-resource foundation")
