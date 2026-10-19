#!/usr/bin/env python3
"""Focused verifier for the Stage 21.7.5b V2 rune lifecycle."""
from __future__ import annotations
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cp=subprocess.run([sys.executable,"-m","unittest","-v","tests_v2.test_rune_lifecycle"],cwd=ROOT)
raise SystemExit(cp.returncode)
