from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def economy_markdown(payload: Mapping[str, Any]) -> str:
    result = payload["economy"]
    lines = [
        "# Simulation Economy Analysis 13.8.0",
        "",
        f"- Runs: {result['runs']}",
        f"- Gold faucets: {result['gold_faucets']}",
        f"- Gold sinks: {result['gold_sinks']}",
        f"- Gold transfers: {result['gold_transfers']}",
        f"- Net gold created: {result['net_gold_created']}",
        f"- Mean final cash: {result['mean_final_cash']}",
        f"- Mean total net worth: {result['mean_total_net_worth']}",
        f"- Asset valuation coverage: {result['asset_coverage']}",
        "",
        "> Player-to-player transfers are reported separately and never counted as faucets or sinks.",
    ]
    return "\n".join(lines) + "\n"


def guild_markdown(payload: Mapping[str, Any]) -> str:
    lines = ["# Simulation Guild Population 13.8.0", ""]
    for item in payload["populations"]:
        lines.extend([
            f"## {item['players']} players",
            "",
            f"- Mode: {item['mode']}",
            f"- Guild EXP: {item['guild_exp']}",
            f"- Guild resource: {item['guild_resource']}",
            f"- Kills: {item['kills']}",
            f"- Contracts: {item['contracts']}",
            "",
        ])
    return "\n".join(lines)
