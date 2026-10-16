"""Executable smoke entrypoint for the isolated ROM V2 skeleton."""
from __future__ import annotations

import json

from rom_v2.bootstrap import build_lifecycle


def main() -> int:
    """Start and stop the skeleton without gameplay or external side effects."""
    lifecycle = build_lifecycle()
    lifecycle.start()
    payload = {
        "status": "ready",
        "application": lifecycle.container.config.application_name,
        "mode": lifecycle.container.config.mode,
        "gameplay_enabled": lifecycle.container.config.gameplay_enabled,
        "telegram_started": False,
        "database_opened": False,
        "background_jobs_started": False,
    }
    print(json.dumps(payload, sort_keys=True))
    lifecycle.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
