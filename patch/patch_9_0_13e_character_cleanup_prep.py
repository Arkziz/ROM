#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]

DB_FILE = ROOT / "db.py"

BACKUP_DIR = ROOT / "backup"
BACKUP_DIR.mkdir(exist_ok=True)

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BACKUP_FILE = (
    BACKUP_DIR /
    f"db_before_character_cleanup_prep_{STAMP}.py"
)

REPORT_FILE = (
    BACKUP_DIR /
    f"CHARACTER_CLEANUP_PREP_{STAMP}.txt"
)

TARGETS = [
    "get_character_name",
    "get_character_class",
    "get_character_class_display",
    "get_character_resource_type",
 