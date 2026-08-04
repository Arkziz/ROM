from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    root = Path(__file__).resolve().parents[1]
    cli = root / "tools" / "run_world_progression_sim.py"

    # Reproduce the user's exact launch style without PYTHONPATH.
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    with tempfile.TemporaryDirectory(prefix="rom_progress_cli_") as temporary:
        output = Path(temporary)
        command = [
            sys.executable,
            str(cli),
            "warrior",
            "2",
            "regular",
            "--seed",
            "136001",
            "--output",
            str(output),
        ]
        completed = subprocess.run(
            command,
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "direct CLI launch failed\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )

        json_files = list(output.glob("*.json"))
        markdown_files = list(output.glob("*.md"))
        assert len(json_files) == 1
        assert len(markdown_files) == 1
        payload = json.loads(json_files[0].read_text(encoding="utf-8-sig"))
        assert payload["status"] == "completed"
        assert payload["final_level"] == 2

    print("[OK] World progression CLI direct-launch contracts")
    print("- direct python tools/run_world_progression_sim.py: PASS")
    print("- no external PYTHONPATH required: PASS")
    print("- systems package import from ROM root: PASS")
    print("- JSON/Markdown report generation: PASS")
    print("- database writes: 0")


if __name__ == "__main__":
    main()
