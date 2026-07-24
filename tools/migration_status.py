#!/usr/bin/env python3
"""Show ROM migration status."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db
from migrations.runner import get_migration_status


def main():
    status = get_migration_status(db.conn)
    print("ROM migration status")
    print("====================")
    print(f"Known:   {len(status['known'])}")
    print(f"Applied: {status['applied_count']}")
    print(f"Pending: {status['pending_count']}")
    print("")

    if status["pending"]:
        print("Pending migrations:")
        for name in status["pending"]:
            print(f"- {name}")
    else:
        print("No pending migrations.")


if __name__ == "__main__":
    main()
