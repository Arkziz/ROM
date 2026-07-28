#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i4e: remove unused regen capture and fix readiness regex."""
from __future__ import annotations
import ast
import base64
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i4e"
CAPTURE_NAME = "_legacy_process_passive_regeneration_before_hp_dynamic_max_fix_v1"
OLD_REGEX_TEXT = 're.compile(r"_legacy_[A-Za-z0-9_]+")'
NEW_REGEX_TEXT = 're.compile(r"(?<![A-Za-z0-9_])_legacy_[A-Za-z0-9_]+")'
PRESERVED_MIGRATION = "migrate_legacy_equipment_to_slots"
POST_AUDIT_SOURCE = base64.b64decode("IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiJST00gOS4wLjEyaTRlOiB2ZXJpZnkgcmVzaWR1YWwgbGVnYWN5IHJlZmVyZW5jZXMgYXJlIGZ1bGx5IGNsZWFuZWQuIiIiCmZyb20gX19mdXR1cmVfXyBpbXBvcnQgYW5ub3RhdGlvbnMKaW1wb3J0IGFzdAppbXBvcnQgcmUKaW1wb3J0IHN5cwpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKClJPT1QgPSBQYXRoKF9fZmlsZV9fKS5yZXNvbHZlKCkucGFyZW50c1sxXQpEQl9QQVRIID0gUk9PVCAvICJkYi5weSIKUkVBRElORVNTX1BBVEggPSBST09UIC8gInRvb2xzIiAvICJkYl9jbGVhbnVwX3JlYWRpbmVzcy5weSIKUkVQT1JUX1BBVEggPSBST09UIC8gIkRCX0NMRUFOVVBfOV8wXzEySTRFX1JFU0lEVUFMX0xFR0FDWV9SRUZTX0NMRUFOVVAubWQiCkVYUEVDVEVEX1BBVFRFUk4gPSByIig/PCFbQS1aYS16MC05X10pX2xlZ2FjeV9bQS1aYS16MC05X10rIgpSRU1PVkVEX0NBUFRVUkUgPSAiX2xlZ2FjeV9wcm9jZXNzX3Bhc3NpdmVfcmVnZW5lcmF0aW9uX2JlZm9yZV9ocF9keW5hbWljX21heF9maXhfdjEiClBSRVNFUlZFRF9NSUdSQVRJT04gPSAibWlncmF0ZV9sZWdhY3lfZXF1aXBtZW50X3RvX3Nsb3RzIgoKCmRlZiBmYWlsKG1lc3NhZ2UpOgogICAgcHJpbnQoZiJbRkFJTF0ge21lc3NhZ2V9IikKICAgIHJhaXNlIFN5c3RlbUV4aXQoMSkKCgpkZWYgbWFpbigpOgogICAgZGJfdGV4dCA9IERCX1BBVEgucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOC1zaWciKQogICAgcmVhZGluZXNzX3RleHQgPSBSRUFESU5FU1NfUEFUSC5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04LXNpZyIpCiAgICB0cmVlID0gYXN0LnBhcnNlKGRiX3RleHQsIGZpbGVuYW1lPXN0cihEQl9QQVRIKSkKCiAgICBpZiBSRU1PVkVEX0NBUFRVUkUgaW4gZGJfdGV4dDoKICAgICAgICBmYWlsKCJ1bnVzZWQgcmVnZW4gY2FwdHVyZSBpcyBzdGlsbCBwcmVzZW50IikKICAgIGlmIFBSRVNFUlZFRF9NSUdSQVRJT04gbm90IGluIGRiX3RleHQ6CiAgICAgICAgZmFpbCgibWlncmF0ZV9sZWdhY3lfZXF1aXBtZW50X3RvX3Nsb3RzIHdhcyByZW1vdmVkIG9yIHJlbmFtZWQiKQogICAgaWYgRVhQRUNURURfUEFUVEVSTiBub3QgaW4gcmVhZGluZXNzX3RleHQ6CiAgICAgICAgZmFpbCgicmVhZGluZXNzIHJlZ2V4IHdhcyBub3QgdXBkYXRlZCB0byB0aGUgaWRlbnRpZmllci1ib3VuZGFyeSBwYXR0ZXJuIikKCiAgICBtYXRjaGVzID0gc29ydGVkKHNldChyZS5jb21waWxlKEVYUEVDVEVEX1BBVFRFUk4pLmZpbmRhbGwoZGJfdGV4dCkpKQogICAgaWYgbWF0Y2hlczoKICAgICAgICBmYWlsKGYicmVhbCBsZWdhY3kgaWRlbnRpZmllcnMgcmVtYWluOiB7bWF0Y2hlc30iKQoKICAgIHJlZ2VuX2RlZnMgPSBbCiAgICAgICAgbm9kZSBmb3Igbm9kZSBpbiB0cmVlLmJvZHkKICAgICAgICBpZiBpc2luc3RhbmNlKG5vZGUsIChhc3QuRnVuY3Rpb25EZWYsIGFzdC5Bc3luY0Z1bmN0aW9uRGVmKSkKICAgICAgICBhbmQgbm9kZS5uYW1lID09ICJwcm9jZXNzX3Bhc3NpdmVfcmVnZW5lcmF0aW9uIgogICAgXQogICAgaWYgbm90IHJlZ2VuX2RlZnM6CiAgICAgICAgZmFpbCgicHJvY2Vzc19wYXNzaXZlX3JlZ2VuZXJhdGlvbiBpcyBtaXNzaW5nIikKICAgIGZpbmFsX3JlZ2VuID0gYXN0LmdldF9zb3VyY2Vfc2VnbWVudChkYl90ZXh0LCByZWdlbl9kZWZzWy0xXSkgb3IgIiIKICAgIGlmICJyZWdlbl9zeXN0ZW0iIG5vdCBpbiBmaW5hbF9yZWdlbjoKICAgICAgICBmYWlsKCJmaW5hbCBwcm9jZXNzX3Bhc3NpdmVfcmVnZW5lcmF0aW9uIGRvZXMgbm90IGRlbGVnYXRlIHRvIHJlZ2VuX3N5c3RlbSIpCgogICAgbWlncmF0aW9uX2RlZnMgPSBbCiAgICAgICAgbm9kZSBmb3Igbm9kZSBpbiB0cmVlLmJvZHkKICAgICAgICBpZiBpc2luc3RhbmNlKG5vZGUsIChhc3QuRnVuY3Rpb25EZWYsIGFzdC5Bc3luY0Z1bmN0aW9uRGVmKSkKICAgICAgICBhbmQgbm9kZS5uYW1lID09IFBSRVNFUlZFRF9NSUdSQVRJT04KICAgIF0KICAgIGlmIGxlbihtaWdyYXRpb25fZGVmcykgIT0gMToKICAgICAgICBmYWlsKGYie1BSRVNFUlZFRF9NSUdSQVRJT059IGRlZmluaXRpb25zPXtsZW4obWlncmF0aW9uX2RlZnMpfSwgZXhwZWN0ZWQgMSIpCgogICAgcmVwb3J0ID0gWwogICAgICAgICIjIFJPTSA5LjAuMTJpNGUgLSBSZXNpZHVhbCBMZWdhY3kgUmVmZXJlbmNlcyBDbGVhbnVwIiwKICAgICAgICAiIiwKICAgICAgICAiIyMgUmVzdWx0IiwKICAgICAgICAiIiwKICAgICAgICAiLSBVbnVzZWQgcmVnZW4gY29tcGF0aWJpbGl0eSBjYXB0dXJlIHJlbW92ZWQ6IHllcyIsCiAgICAgICAgIi0gUmVhZGluZXNzIHJlZ2V4IGlkZW50aWZpZXIgYm91bmRhcnkgZml4ZWQ6IHllcyIsCiAgICAgICAgIi0gYG1pZ3JhdGVfbGVnYWN5X2VxdWlwbWVudF90b19zbG90c2AgcHJlc2VydmVkOiB5ZXMiLAogICAgICAgICItIFJlYWwgYF9sZWdhY3lfKmAgaWRlbnRpZmllcnMgcmVtYWluaW5nIGluIGBkYi5weWA6IDAiLAogICAgICAgICItIEZpbmFsIGBwcm9jZXNzX3Bhc3NpdmVfcmVnZW5lcmF0aW9uYCBkZWxlZ2F0ZXMgdG8gYHN5c3RlbXMucmVnZW5fc3lzdGVtYDogeWVzIiwKICAgICAgICAiLSBEYXRhYmFzZSBtdXRhdGlvbnMgcGVyZm9ybWVkIGJ5IHRoaXMgdmVyaWZpY2F0aW9uOiAwIiwKICAgICAgICAiIiwKICAgICAgICAiIyMgRXhwZWN0ZWQgcmVhZGluZXNzIiwKICAgICAgICAiIiwKICAgICAgICAiLSBgbGVnYWN5X3JlZnNgOiAwIiwKICAgICAgICAiLSBgdW5zYWZlX2RlbGV0ZWA6IDAiLAogICAgICAgICIiLAogICAgXQogICAgUkVQT1JUX1BBVEgud3JpdGVfdGV4dCgiXG4iLmpvaW4ocmVwb3J0KSwgZW5jb2Rpbmc9InV0Zi04IikKCiAgICBwcmludCgiW09LXSByZXNpZHVhbCBsZWdhY3kgcmVmcyBwb3N0LWNsZWFudXAiKQogICAgcHJpbnQoIi0gcmVhbCBsZWdhY3kgaWRlbnRpZmllcnM6IDAiKQogICAgcHJpbnQoIi0gdW51c2VkIHJlZ2VuIGNhcHR1cmU6IHJlbW92ZWQiKQogICAgcHJpbnQoIi0gcmVhZGluZXNzIHJlZ2V4IGJvdW5kYXJ5OiBmaXhlZCIpCiAgICBwcmludCgiLSBtaWdyYXRlX2xlZ2FjeV9lcXVpcG1lbnRfdG9fc2xvdHMgcHJlc2VydmVkOiB5ZXMiKQogICAgcHJpbnQoIi0gcmVnZW4gc3lzdGVtIGRlbGVnYXRpb246IE9LIikKICAgIHByaW50KCItIGRhdGFiYXNlIG11dGF0aW9uczogMCIpCiAgICBwcmludChmIi0gcmVwb3J0OiB7UkVQT1JUX1BBVEh9IikKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgbWFpbigpCg==").decode("utf-8")


def fail(message):
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root():
    here = Path(__file__).resolve()
    for root in (here.parent.parent, Path.cwd(), Path.cwd().parent):
        root = root.resolve()
        if (root / "db.py").is_file() and (root / "tools" / "db_cleanup_readiness.py").is_file():
            return root
    fail("Не знайдено корінь ROM.")


def find_capture_try(tree):
    matches = []
    for node in tree.body:
        if not isinstance(node, ast.Try):
            continue
        names = {
            sub.id for sub in ast.walk(node)
            if isinstance(sub, ast.Name)
        }
        if CAPTURE_NAME in names:
            matches.append(node)
    return matches


def main():
    root = find_root()
    db_path = root / "db.py"
    readiness_path = root / "tools" / "db_cleanup_readiness.py"
    audit_path = root / "tools" / "audit_residual_legacy_refs.py"

    db_source = db_path.read_text(encoding="utf-8-sig")
    readiness_source = readiness_path.read_text(encoding="utf-8-sig")

    already_clean = (
        CAPTURE_NAME not in db_source
        and NEW_REGEX_TEXT in readiness_source
        and OLD_REGEX_TEXT not in readiness_source
    )
    if already_clean:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірку.")
        if not audit_path.is_file():
            audit_path.write_text(POST_AUDIT_SOURCE, encoding="utf-8")
        result = subprocess.run([sys.executable, str(audit_path)], cwd=root)
        raise SystemExit(result.returncode)

    if PRESERVED_MIGRATION not in db_source:
        fail(f"Не знайдено {PRESERVED_MIGRATION}; db.py не змінено.")

    db_tree = ast.parse(db_source, filename=str(db_path))
    capture_blocks = find_capture_try(db_tree)
    if len(capture_blocks) != 1:
        fail(f"Regen capture-блоків знайдено {len(capture_blocks)} замість 1.")

    capture_node = capture_blocks[0]
    lines = db_source.splitlines(keepends=True)
    del lines[capture_node.lineno - 1:capture_node.end_lineno]
    updated_db = "".join(lines)

    try:
        updated_tree = ast.parse(updated_db, filename=str(db_path))
    except SyntaxError as exc:
        fail(f"db.py після очищення не пройшов AST-перевірку: {exc}")

    if CAPTURE_NAME in updated_db:
        fail("Після очищення Regen capture все ще присутній.")
    if PRESERVED_MIGRATION not in updated_db:
        fail(f"Патч зачепив {PRESERVED_MIGRATION}; запис скасовано.")

    regen_defs = [
        node for node in updated_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "process_passive_regeneration"
    ]
    if not regen_defs:
        fail("Після очищення відсутній process_passive_regeneration.")
    final_regen = ast.get_source_segment(updated_db, regen_defs[-1]) or ""
    if "regen_system" not in final_regen:
        fail("Фінальний process_passive_regeneration не делегує в regen_system.")

    old_count = readiness_source.count(OLD_REGEX_TEXT)
    new_count = readiness_source.count(NEW_REGEX_TEXT)
    if old_count != 1 or new_count != 0:
        fail(
            "Readiness regex має неочікуваний стан: "
            f"old={old_count}, new={new_count}. Файли не змінено."
        )
    updated_readiness = readiness_source.replace(OLD_REGEX_TEXT, NEW_REGEX_TEXT, 1)
    try:
        ast.parse(updated_readiness, filename=str(readiness_path))
    except SyntaxError as exc:
        fail(f"Оновлений readiness tool не пройшов AST-перевірку: {exc}")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup = backup_dir / f"db.py_{PATCH_ID}_regen_capture_cleanup_{stamp}.bak"
    readiness_backup = backup_dir / f"tools_db_cleanup_readiness.py_{PATCH_ID}_regex_fix_{stamp}.bak"
    shutil.copy2(db_path, db_backup)
    shutil.copy2(readiness_path, readiness_backup)
    audit_backup = None
    if audit_path.exists():
        audit_backup = backup_dir / f"tools_audit_residual_legacy_refs.py_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(audit_path, audit_backup)

    db_temp = db_path.with_name(".db.i4e.tmp")
    readiness_temp = readiness_path.with_name(".db_cleanup_readiness.i4e.tmp")
    try:
        db_temp.write_text(updated_db, encoding="utf-8")
        readiness_temp.write_text(updated_readiness, encoding="utf-8")
        os.replace(db_temp, db_path)
        os.replace(readiness_temp, readiness_path)
        audit_path.write_text(POST_AUDIT_SOURCE, encoding="utf-8")

        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(readiness_path), doraise=True)
        py_compile.compile(str(audit_path), doraise=True)

        audit_result = subprocess.run([sys.executable, str(audit_path)], cwd=root)
        if audit_result.returncode != 0:
            raise RuntimeError(f"post-cleanup audit exit code {audit_result.returncode}")

        readiness_result = subprocess.run(
            [sys.executable, str(readiness_path)], cwd=root,
            text=True, capture_output=True
        )
        print(readiness_result.stdout, end="")
        if readiness_result.returncode != 0:
            raise RuntimeError(f"readiness exit code {readiness_result.returncode}")
        if "legacy_refs: 0" not in readiness_result.stdout:
            raise RuntimeError("readiness не підтвердив legacy_refs: 0")
        if "unsafe_delete: 0" not in readiness_result.stdout:
            raise RuntimeError("readiness не підтвердив unsafe_delete: 0")
    except Exception as exc:
        shutil.copy2(db_backup, db_path)
        shutil.copy2(readiness_backup, readiness_path)
        if audit_backup is not None:
            shutil.copy2(audit_backup, audit_path)
        elif audit_path.exists():
            audit_path.unlink()
        for temp in (db_temp, readiness_temp):
            if temp.exists():
                temp.unlink()
        fail(f"Перевірка не пройдена; файли відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Видалено невикористаний Regen compatibility capture.")
    print("✅ Виправлено межу ідентифікатора в readiness regex.")
    print(f"✅ {PRESERVED_MIGRATION} збережено без змін.")
    print("✅ Readiness підтвердив legacy_refs: 0 та unsafe_delete: 0.")
    print("Резервні копії:")
    print(f"   {db_backup.relative_to(root)}")
    print(f"   {readiness_backup.relative_to(root)}")
    if audit_backup is not None:
        print(f"   {audit_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./db.py")
    print("   python -m py_compile ./tools/db_cleanup_readiness.py")
    print("   python ./tools/audit_residual_legacy_refs.py")
    print("   python ./tools/smoke_test_regen_contracts.py")
    print("   python ./tools/smoke_test_equipment_readonly_core.py")
    print("   python ./tools/smoke_test_player_contracts.py")
    print("   python ./tools/smoke_test_player_combat_stats.py")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
