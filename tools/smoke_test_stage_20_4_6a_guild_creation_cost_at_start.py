#!/usr/bin/env python3
from __future__ import annotations
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / "handlers/guild.py").read_text(encoding="utf-8-sig")
TREE = ast.parse(TEXT)

def function_source(name):
    nodes = [node for node in TREE.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    assert len(nodes) == 1, (name, len(nodes))
    return ast.get_source_segment(TEXT, nodes[0]) or ""

def main():
    prompt = function_source("build_guild_create_name_prompt")
    confirm = function_source("build_guild_create_confirm_text")
    assert "def build_guild_create_name_prompt(user_id=None):" in prompt
    assert "get_guild_creation_terms(user_id)" in prompt
    assert "Вартість створення: {terms['cost_gold']:.2f}" in prompt
    assert "Початковий ліміт: {terms['member_limit']} учасників." in prompt
    assert "Крок 1/4 — назва гільдії." in prompt
    assert "terms['cost_gold']:.2f" in confirm
    assert "Крок 4/4 — підтвердження." in confirm
    assert TEXT.count("build_guild_create_name_prompt(user_id)") == 2
    print("[OK] Guild creation start prompt shows canonical cost and member limit")

if __name__ == "__main__":
    main()
