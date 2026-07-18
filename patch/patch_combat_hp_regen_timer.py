from pathlib import Path
from datetime import datetime
import py_compile


PATCH_NAME = "combat_hp_regen_timer"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"

    backup_path.write_text(
        target.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    return backup_path


def patch_db(root):
    target = root / "db.py"

    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")

    original = target.read_text(encoding="utf-8")
    text = original

    marker = "# ✅ FINAL OVERRIDE: SET CURRENT HP RESETS PASSIVE REGEN TIMER"

    if marker in text:
        print("ℹ️ db.py: final set_current_hp override вже є, пропускаю додавання.")
        return None

    backup_path = make_backup(root, target)

    override = r'''

# ==============================
# ✅ FINAL OVERRIDE: SET CURRENT HP RESETS PASSIVE REGEN TIMER
# ==============================

def set_current_hp(user_id, hp):
    """
    Безпечно встановлює поточне HP гравця.

    Важливо:
    після будь-якої ручної зміни HP оновлюємо last_hp_regen_update,
    щоб пасивна регенерація не "наздоганяла" час бою одразу після бою.

    Це потрібно для правил:
    - під час бою пасивний реген не накопичується;
    - після смерті герой лишається з 1 HP;
    - після завершення бою таймер пасивної регенерації стартує заново.
    """

    from datetime import datetime

    init_hp_regen_system()

    max_hp = get_max_hp(user_id)

    try:
        hp = int(hp)
    except Exception:
        hp = max_hp

    if max_hp <= 0:
        max_hp = 1

    hp = max(0, min(max_hp, hp))

    hp_full_notified = 1 if hp >= max_hp else 0

    cursor.execute("""
    UPDATE users
    SET hp=?,
        last_hp_regen_update=?,
        hp_full_notified=?
    WHERE user_id=?
    """, (
        hp,
        datetime.now().isoformat(),
        hp_full_notified,
        user_id
    ))

    conn.commit()

    return hp
'''

    text = text.rstrip() + "\n" + override + "\n"

    target.write_text(text, encoding="utf-8")

    return backup_path


def patch_combat(root):
    target = root / "handlers" / "combat.py"

    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/combat.py")

    original = target.read_text(encoding="utf-8")
    text = original

    backup_path = make_backup(root, target)

    changed = False

    # 1. На всяк випадок гарантуємо, що смерть ставить HP = 1.
    old = "set_current_hp(user_id, player_max_hp)"
    new = "set_current_hp(user_id, 1)"

    count_death = text.count(old)

    if count_death > 0:
        text = text.replace(old, new)
        changed = True
        print(f"✅ combat.py: замінено death HP full -> 1, рядків: {count_death}")
    else:
        print("ℹ️ combat.py: set_current_hp(user_id, player_max_hp) не знайдено. Можливо, смерть уже ставить HP = 1.")

    # 2. Скидаємо таймер пасивного HP-регену на старті бою.
    # Це блокує накопичення пасивного відновлення під час бою.
    anchor = '''        mob["player_hp"] = current_hp
        mob["player_max_hp"] = max_hp
'''

    insert = '''        mob["player_hp"] = current_hp
        mob["player_max_hp"] = max_hp

        # Бій почався: пасивна регенерація HP не має накопичуватись під час бою.
        # set_current_hp() також оновлює last_hp_regen_update.
        set_current_hp(user_id, current_hp)
'''

    if "пасивна регенерація HP не має накопичуватись під час бою" in text:
        print("ℹ️ combat.py: reset regen timer at combat start вже є, пропускаю.")
    else:
        count_anchor = text.count(anchor)

        if count_anchor <= 0:
            print("⚠️ combat.py: не знайдено anchor для старту бою. Пропускаю вставку reset timer.")
        else:
            # Міняємо тільки перший збіг — це старт полювання.
            text = text.replace(anchor, insert, 1)
            changed = True
            print("✅ combat.py: додано reset пасивного HP-регену на старті бою.")

    if changed:
        target.write_text(text, encoding="utf-8")
    else:
        print("ℹ️ combat.py: змін не внесено.")

    return backup_path


def compile_file(path, original_text=None):
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as error:
        if original_text is not None:
            path.write_text(original_text, encoding="utf-8")

        raise SystemExit(
            f"❌ Помилка py_compile для {path}:\n{error}"
        )


def main():
    root = Path(__file__).resolve().parents[1]

    db_path = root / "db.py"
    combat_path = root / "handlers" / "combat.py"

    db_original = db_path.read_text(encoding="utf-8")
    combat_original = combat_path.read_text(encoding="utf-8")

    db_backup = patch_db(root)
    combat_backup = patch_combat(root)

    try:
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(combat_path), doraise=True)
    except Exception as error:
        db_path.write_text(db_original, encoding="utf-8")
        combat_path.write_text(combat_original, encoding="utf-8")

        raise SystemExit(
            "❌ Після патча виникла помилка компіляції.\n"
            "Файли db.py і handlers/combat.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("")
    print("✅ Патч застосовано успішно.")
    print("✅ db.py пройшов py_compile.")
    print("✅ handlers/combat.py пройшов py_compile.")

    if db_backup:
        print(f"✅ Backup db.py: {db_backup}")

    if combat_backup:
        print(f"✅ Backup combat.py: {combat_backup}")

    print("")
    print("Результат:")
    print("- після смерті HP має залишатися 1;")
    print("- пасивна регенерація більше не має нараховуватися за час бою;")
    print("- після бою таймер пасивної регенерації стартує заново.")


if __name__ == "__main__":
    main()