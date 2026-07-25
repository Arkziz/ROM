from pathlib import Path
from datetime import datetime
import ast
import py_compile

PATCH_NAME = "9_0_12e1_energy_system_real_implementation"
TARGET_FUNCTIONS = [
    "init_energy_system",
    "get_user_energy",
    "consume_energy_for_hunt",
    "restore_energy_for_test",
    "get_users_for_energy_full_notification",
]


def backup(root, path):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(path.relative_to(root)).replace("\\", "_").replace("/", "_")
    dst = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    dst.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return dst


def source_segment(text, node):
    lines = text.splitlines(keepends=True)
    return "".join(lines[node.lineno - 1:node.end_lineno]).rstrip() + "\n"


def collect_final_functions(db_text):
    tree = ast.parse(db_text)
    found = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in TARGET_FUNCTIONS:
            found[node.name] = source_segment(db_text, node)
    return found


def build_energy_module(functions):
    required = [name for name in ("init_energy_system", "get_user_energy") if name not in functions]
    if required:
        raise RuntimeError(f"Required energy functions not found in db.py: {required}")

    chunks = [
        '\"\"\"Energy/fatigue domain implementation extracted from db.py.\n\n'
        'Fatigue scale: 0 = fully rested, 40 = fully fatigued.\n'
        'db.py remains a compatibility facade.\n\"\"\"\n',
        'from datetime import datetime, timedelta\n',
        'from importlib import import_module\n\n',
        'ENERGY_MAX = 40\n',
        'ENERGY_REGEN_MINUTES = 5\n\n',
        'def _db():\n    return import_module("db")\n\n',
        'class _ConnProxy:\n'
        '    def __getattr__(self, name):\n'
        '        return getattr(_db().conn, name)\n\n'
        'class _CursorProxy:\n'
        '    def __getattr__(self, name):\n'
        '        return getattr(_db().cursor, name)\n\n'
        'conn = _ConnProxy()\n'
        'cursor = _CursorProxy()\n\n',
    ]
    for name in TARGET_FUNCTIONS:
        if name in functions:
            chunks.append(functions[name])
            chunks.append("\n")
    chunks.append(
        'def get_energy_contract_snapshot(user_id):\n'
        '    result = get_user_energy(user_id)\n'
        '    return {"result": result, "result_type": type(result).__name__}\n'
    )
    return "".join(chunks)


def remove_old_energy_facade(db_text):
    marker = "# ✅ REFACTOR 9.0.4 ENERGY SYSTEM FACADE"
    pos = db_text.find(marker)
    if pos < 0:
        return db_text
    start = db_text.rfind("# ==============================", 0, pos)
    if start < 0:
        start = pos
    candidates = [
        db_text.find("# ✅ ROM 9.0.2b HP MAX SYNC DB WRAPPER V1", pos + 1),
        db_text.find("# ✅ ROM 9.0.2c HP REGEN DYNAMIC MAX FIX V1", pos + 1),
        db_text.find("# ✅ REFACTOR 9.0.5: REGEN SYSTEM FACADE", pos + 1),
    ]
    candidates = [value for value in candidates if value >= 0]
    if not candidates:
        raise RuntimeError("Could not find end of old energy facade")
    end_marker = min(candidates)
    end = db_text.rfind("# ==============================", start, end_marker)
    if end <= start:
        end = end_marker
    return db_text[:start].rstrip() + "\n\n" + db_text[end:].lstrip()


def append_db_wrappers(db_text, functions):
    marker = "# ✅ ROM 9.0.12e1 ENERGY SYSTEM REAL IMPLEMENTATION WRAPPERS V2"
    if marker in db_text:
        raise RuntimeError("9.0.12e1 already present")
    lines = [
        "\n\n# ==============================\n",
        marker + "\n",
        "# ==============================\n\n",
        "def _energy_system_v2():\n",
        "    from systems import energy_system as _mod\n",
        "    return _mod\n\n",
    ]
    for name in TARGET_FUNCTIONS:
        if name in functions:
            lines += [
                f"def {name}(*args, **kwargs):\n",
                f"    return _energy_system_v2().{name}(*args, **kwargs)\n\n",
            ]
    return db_text.rstrip() + "".join(lines)


def write_smoke_test(root):
    path = root / "tools" / "smoke_test_energy_contracts.py"
    path.parent.mkdir(exist_ok=True)
    content = '''from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db
uid = int(os.environ.get("ROM_TEST_USER_ID", "243129101"))

for name in ("init_energy_system", "get_user_energy"):
    if not hasattr(db, name):
        raise SystemExit(f"[FAIL] missing energy API: {name}")

db.init_energy_system()
result = db.get_user_energy(uid)
if isinstance(result, dict):
    value = result.get("energy", result.get("fatigue"))
elif isinstance(result, (tuple, list)):
    value = result[0] if result else None
else:
    value = result
try:
    value = int(value)
except Exception as exc:
    raise SystemExit(f"[FAIL] invalid energy result: {result!r}") from exc
if not 0 <= value <= 40:
    raise SystemExit(f"[FAIL] fatigue out of range: {value}")
print("[OK] energy runtime contracts")
print("- result type:", type(result).__name__)
print("- fatigue:", value, "/ 40")
print("- rule: 0=rested, 40=fully fatigued")
'''
    path.write_text(content, encoding="utf-8")
    return path


def update_check_imports(root):
    path = root / "tools" / "check_imports.py"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    old = text
    if '"systems/energy_system.py"' not in text:
        anchor = '"systems/regen_system.py",'
        if anchor in text:
            text = text.replace(anchor, '"systems/energy_system.py",\n    ' + anchor, 1)
    if '"systems.energy_system"' not in text:
        anchor = '"systems.regen_system",'
        if anchor in text:
            text = text.replace(anchor, '"systems.energy_system",\n    ' + anchor, 1)
    if text != old:
        backup(root, path)
        path.write_text(text, encoding="utf-8")
    return path


def main():
    root = Path(__file__).resolve().parents[1]
    db_path = root / "db.py"
    energy_path = root / "systems" / "energy_system.py"
    if not db_path.exists() or not energy_path.exists():
        raise SystemExit("❌ db.py or systems/energy_system.py not found")

    db_original = db_path.read_text(encoding="utf-8")
    energy_original = energy_path.read_text(encoding="utf-8")
    db_backup = backup(root, db_path)
    energy_backup = backup(root, energy_path)

    try:
        functions = collect_final_functions(db_original)
        energy_new = build_energy_module(functions)
        db_new = append_db_wrappers(remove_old_energy_facade(db_original), functions)
        energy_path.write_text(energy_new, encoding="utf-8")
        db_path.write_text(db_new, encoding="utf-8")
        smoke_path = write_smoke_test(root)
        check_path = update_check_imports(root)
        py_compile.compile(str(energy_path), doraise=True)
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(smoke_path), doraise=True)
        if check_path:
            py_compile.compile(str(check_path), doraise=True)
    except Exception as exc:
        db_path.write_text(db_original, encoding="utf-8")
        energy_path.write_text(energy_original, encoding="utf-8")
        raise SystemExit(f"❌ Patch failed; files restored.\n{exc}")

    print("✅ Patch 9.0.12e1 applied successfully.")
    print("✅ Energy logic now lives in systems/energy_system.py without _legacy energy delegation.")
    print("✅ notifications.py was not modified.")
    print("Backup:")
    print(f"- {db_backup}")
    print(f"- {energy_backup}")
    print("Checks:")
    print(r"python -m py_compile .\systems\energy_system.py")
    print(r"python -m py_compile .\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/smoke_test_energy_contracts.py")
    print("python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
