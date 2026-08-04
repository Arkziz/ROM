from __future__ import annotations

import json
from pathlib import Path

from systems.simulation.production_parity import run_required_parity, source_dependency_report


def main():
    parity = run_required_parity()
    dependencies = source_dependency_report()
    output = Path("MD")
    output.mkdir(exist_ok=True)
    (output / "SIMULATION_CANONICAL_RULES_PARITY_13_2_0.json").write_text(
        json.dumps(parity, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Simulation Canonical Rules Parity 13.2.0", "",
        f"Verdict: **{parity['verdict']}**", "",
        f"- Cases: **{parity['cases']}**",
        f"- Passed: **{parity['passed']}**",
        f"- Failed: **{parity['failed']}**",
        f"- Result SHA-256: `{parity['sha256']}`", "",
        "## Canonical sources", "",
    ]
    for item in dependencies["rules"]:
        lines.append(f"- `{item['rule']}` -> `{item['qualified_name']}` `{item['signature']}` at line {item['source_line']}; RNG injected: `{item['rng_injected']}`")
    failed = [item for item in parity["results"] if not item["passed"]]
    lines += ["", "## Findings", ""]
    if failed:
        for item in failed:
            lines.append(f"- `{item['case_id']}`: {item['error']}")
    else:
        lines.append("- No parity findings.")
    (output / "SIMULATION_CANONICAL_RULES_PARITY_13_2_0.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if parity["verdict"] != "PASS":
        raise SystemExit(2)
    print("[OK] Canonical parity report generated")
    print(f"- cases: {parity['cases']}")
    print("- verdict: PASS")


if __name__ == "__main__":
    main()
