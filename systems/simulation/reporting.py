from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Dict, Tuple


def _safe_run_id(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "simulation"))
    return result.strip("._") or "simulation"


def canonical_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def payload_digest(payload: Dict[str, Any]) -> str:
    compact = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(compact.encode("utf-8")).hexdigest()


def build_markdown_report(payload: Dict[str, Any]) -> str:
    config = payload.get("config", {})
    state = payload.get("state", {})
    character = state.get("character", {})
    inventory = state.get("inventory", {})
    metrics = payload.get("metrics", {})
    lines = [
        "# ROM Simulation Report",
        "",
        f"- Run ID: `{payload.get('run_id', '')}`",
        f"- Status: **{payload.get('status', '')}**",
        f"- Schema: `{payload.get('schema_version', '')}`",
        f"- Seed: `{payload.get('seed', '')}`",
        f"- Config fingerprint: `{payload.get('config_fingerprint', '')}`",
        f"- Payload SHA-256: `{payload_digest(payload)}`",
        f"- Clock: `{payload.get('clock_start', '')}` -> `{payload.get('clock_end', '')}`",
        "",
        "## Configuration",
        "",
        f"- Class: `{config.get('character_class', '')}`",
        f"- Target level: `{config.get('target_level', '')}`",
        f"- Profile: `{config.get('profile_key', '')}`",
        f"- Mode: `{config.get('mode', '')}`",
        f"- Inventory capacity: `{config.get('inventory_capacity', '')}`",
        f"- PvP enabled: `{config.get('pvp_enabled', False)}`",
        "",
        "## Character snapshot",
        "",
        f"- Level: `{character.get('level', '')}`",
        f"- EXP: `{character.get('exp', '')}`",
        f"- Gold: `{character.get('gold', '')}`",
        f"- HP: `{character.get('hp', '')}/{character.get('max_hp', '')}`",
        f"- MP: `{character.get('mp', '')}/{character.get('max_mp', '')}`",
        f"- Energy: `{character.get('energy', '')}`",
        "",
        "## Inventory snapshot",
        "",
        f"- Used slots: `{len(inventory.get('items', []))}`",
        f"- Capacity: `{inventory.get('capacity', '')}`",
        "",
        "## Metrics",
        "",
    ]
    for name, value in sorted(metrics.get("counters", {}).items()):
        lines.append(f"- Counter `{name}`: `{value}`")
    for name, value in sorted(metrics.get("totals", {}).items()):
        lines.append(f"- Total `{name}`: `{value}`")
    for name, value in sorted(metrics.get("gauges", {}).items()):
        lines.append(f"- Gauge `{name}`: `{value}`")
    if not any(metrics.get(key) for key in ("counters", "totals", "gauges")):
        lines.append("- No gameplay metrics yet. Stage 13.1 validates only the foundation.")
    return "\n".join(lines) + "\n"


def write_simulation_reports(payload: Dict[str, Any], output_dir: Path) -> Tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_run_id(payload.get("run_id", "simulation"))
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_tmp = json_path.with_suffix(json_path.suffix + ".tmp")
    md_tmp = md_path.with_suffix(md_path.suffix + ".tmp")
    json_tmp.write_text(canonical_json(payload), encoding="utf-8")
    md_tmp.write_text(build_markdown_report(payload), encoding="utf-8")
    json_tmp.replace(json_path)
    md_tmp.replace(md_path)
    return json_path, md_path
