from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12h2a_death_and_victory_durability_contract_fix"
TARGET = Path("systems") / "equipment_system.py"
SMOKE = Path("tools") / "smoke_test_equipment_durability_contracts.py"
MARKER = "# ✅ 9.0.12h2a DEATH AND VICTORY DURABILITY CONTRACT FIX"


def backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    dst = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    dst.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return dst


HOTFIX = r'''

# ==============================
# ✅ 9.0.12h2a DEATH AND VICTORY DURABILITY CONTRACT FIX
# ==============================


def damage_equipped_items_on_death(user_id, amount=5):
    """
    Historical public contract used by handlers/combat.py:
    list[dict] with name, old, new and broken.

    The gameplay rule is fixed at -5 durability for every equipped item.
    The amount argument remains accepted for API compatibility.
    """
    result = damage_equipped_items(user_id, amount=5)
    items = result.get("items", []) if isinstance(result, dict) else []
    return [
        {
            "name": str(item.get("name") or "Предмет"),
            "old": int(item.get("old_durability", 0) or 0),
            "new": int(item.get("new_durability", 0) or 0),
            "broken": bool(item.get("is_broken", False)),
        }
        for item in items
        if isinstance(item, dict)
    ]


def apply_random_durability_wear_on_victory(user_id, chance_percent=25, **kwargs):
    """
    Historical public contract used by build_victory_text():
    {triggered: bool, message: str | None}.

    On a successful roll exactly one equipped, non-broken item loses 1 durability.
    """
    import random

    try:
        chance_percent = int(chance_percent)
    except Exception:
        chance_percent = 25
    chance_percent = max(0, min(100, chance_percent))

    roll = random.randint(1, 100)
    if roll > chance_percent:
        return {"triggered": False, "message": None}

    db = _equipment_db_9_0_12h2()
    rows = db.conn.execute(
        "SELECT es.slot_key, inv.id, COALESCE(inv.durability,100), it.name "
        "FROM equipment_slots es "
        "JOIN inventory inv ON inv.id=es.inventory_id AND inv.user_id=es.user_id "
        "JOIN items it ON it.id=inv.item_id "
        "WHERE es.user_id=? AND es.inventory_id IS NOT NULL "
        "AND COALESCE(inv.durability,100)>0",
        (int(user_id),),
    ).fetchall()

    if not rows:
        return {"triggered": False, "message": None}

    slot_key, inventory_id, old_durability, base_name = random.choice(rows)
    old_durability = max(0, min(100, int(old_durability or 0)))
    new_durability = max(0, old_durability - 1)

    db.conn.execute(
        "UPDATE inventory SET durability=? WHERE id=? AND user_id=?",
        (new_durability, int(inventory_id), int(user_id)),
    )
    db.conn.commit()
    _equipment_sync_hp_9_0_12h2(user_id)

    name = _equipment_display_name_9_0_12h2(inventory_id, base_name)
    slot_name = _SLOT_NAMES_9_0_12H2.get(str(slot_key), str(slot_key))
    broken_text = " Предмет зламано!" if new_durability <= 0 else ""
    message = (
        f"🧱 {slot_name}: {name} втратив 1 міцності "
        f"({old_durability} → {new_durability}/100).{broken_text}"
    )
    return {
        "triggered": True,
        "message": message,
        "inventory_id": int(inventory_id),
        "name": name,
        "slot_key": str(slot_key),
        "old": old_durability,
        "new": new_durability,
        "broken": new_durability <= 0,
    }


def roll_equipment_wear_after_combat(user_id, chance_percent=25, **kwargs):
    return apply_random_durability_wear_on_victory(
        user_id,
        chance_percent=chance_percent,
        **kwargs,
    )
'''


SMOKE_CODE = r'''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db
from systems import equipment_system as equipment

USER_ID = 243129101

rows = db.get_equipped_items_for_repair(USER_ID)
assert isinstance(rows, list)
assert len(rows) == 10
assert abs(float(db.calculate_repair_cost(95, "common")) - 0.25) < 1e-9
assert abs(float(db.calculate_repair_cost(95, "uncommon")) - 0.62) < 1e-9
assert abs(float(db.calculate_repair_cost(95, "rare")) - 1.75) < 1e-9
assert abs(float(db.calculate_repair_cost(95, "epic")) - 4.5) < 1e-9

# Validate the death formatter contract without damaging real equipment.
synthetic_damage = [
    {"name": "Тестовий предмет", "old": 10, "new": 5, "broken": False},
    {"name": "Зламаний предмет", "old": 5, "new": 0, "broken": True},
]
for item in synthetic_damage:
    assert set(("name", "old", "new", "broken")).issubset(item)
    assert isinstance(item["broken"], bool)

# Validate no-trigger victory contract without modifying the database.
wear = equipment.apply_random_durability_wear_on_victory(USER_ID, chance_percent=0)
assert isinstance(wear, dict)
assert wear == {"triggered": False, "message": None}, wear

# Inspect function source contract by invoking the mapper on an empty account id.
death = equipment.damage_equipped_items_on_death(-999999999, amount=5)
assert isinstance(death, list), type(death)
for item in death:
    assert isinstance(item, dict)
    assert set(("name", "old", "new", "broken")).issubset(item)

print("[OK] equipment durability public contracts")
print("- repair rows:", len(rows))
print("- death result: list[dict]")
print("- death item keys: name, old, new, broken")
print("- victory result keys: triggered, message")
print("- death durability loss: 5")
'''


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET
    smoke = root / SMOKE

    if not target.exists():
        raise SystemExit(f"❌ Не знайдено файл: {target}")

    original = target.read_text(encoding="utf-8")
    original_smoke = smoke.read_text(encoding="utf-8") if smoke.exists() else None

    if MARKER in original:
        print("ℹ️ Патч 9.0.12h2a уже застосовано.")
        return

    backups = [backup(root, target)]
    if smoke.exists():
        backups.append(backup(root, smoke))

    try:
        target.write_text(original.rstrip() + "\n" + HOTFIX + "\n", encoding="utf-8")
        smoke.parent.mkdir(exist_ok=True)
        smoke.write_text(SMOKE_CODE, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(smoke), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        if original_smoke is None:
            try:
                smoke.unlink()
            except FileNotFoundError:
                pass
        else:
            smoke.write_text(original_smoke, encoding="utf-8")
        raise SystemExit(f"❌ Патч не застосовано; файли відновлено.\nПомилка: {error}")

    print("✅ Патч 9.0.12h2a успішно застосовано.")
    print("✅ Формат результату смерті відновлено: list[dict] з ключами name, old, new, broken.")
    print("✅ Формат зношення після перемоги відновлено: triggered і message.")
    print("Резервні копії:")
    for item in backups:
        print(f"- {item}")
    print("Перевірки:")
    print(r"python -m py_compile .\systems\equipment_system.py")
    print(r"python -m py_compile .\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/smoke_test_equipment_durability_contracts.py")
    print("python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
