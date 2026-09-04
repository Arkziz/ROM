#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "systems" / "guild_system.py"
source = SOURCE_PATH.read_text(encoding="utf-8-sig")
tree = ast.parse(source, filename=str(SOURCE_PATH))
lookup_nodes = [
    node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "get_guild_by_name_or_tag"
]
assert len(lookup_nodes) == 1
lookup_source = ast.get_source_segment(source, lookup_nodes[0]) or ""
assert "name_norm = normalize_guild_name_key(value)" in lookup_source
assert "name_norm = normalize_guild_name(value)" not in lookup_source
assert "tag_norm = normalize_guild_tag(value)" in lookup_source

# Execute only the two normalization functions, not the full production module.
function_names = {"normalize_guild_name", "normalize_guild_name_key"}
selected = [
    node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name in function_names
]
assert {node.name for node in selected} == function_names
module = ast.Module(body=selected, type_ignores=[])
ast.fix_missing_locations(module)
namespace = {}
exec(compile(module, "guild_name_key_contract", "exec"), namespace)
normalize_key = namespace["normalize_guild_name_key"]
for value in ("Test", "test", "TEST", "TeSt", " Test "):
    assert normalize_key(value) == "test", (value, normalize_key(value))

for required in (
    "normalize_guild_name_key",
    "validate_guild_name_contract",
    "validate_guild_icon_contract",
    "validate_guild_tag_contract",
    "validate_guild_create_input",
):
    assert len([
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == required
    ]) == 1, required

print("PASS: Test/test/TEST/TeSt normalize to name_norm=test; lookup, tag, icon and name contracts preserved")
