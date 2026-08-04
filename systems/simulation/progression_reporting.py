from __future__ import annotations
import json
from pathlib import Path
from .progression_models import ProgressionResult


def write_progression_report(result: ProgressionResult, output_dir: Path):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{result.run_id}.json"
    md_path = output_dir / f"{result.run_id}.md"
    payload = result.to_dict()
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# Progression Simulation {result.run_id}", "",
        f"- Status: **{result.status}**", f"- Class: **{result.character_class}**",
        f"- Profile: **{result.profile}**", f"- Level: **{result.final_level}/{result.target_level}**",
        f"- Days: **{result.days}**", f"- Battles: **{result.battles}**",
        f"- Wins: **{result.wins}**", f"- Deaths: **{result.deaths}**",
        f"- Energy spent: **{result.energy_spent}**", f"- Energy regenerated: **{result.energy_regenerated}**",
        f"- EXP gained: **{result.exp_gained}**", f"- Gold gained: **{result.gold_gained:.2f}**",
        f"- Final gold: **{result.final_gold:.2f}**", f"- Free inventory slots: **{result.final_free_slots}**",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path
