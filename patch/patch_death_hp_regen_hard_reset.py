from pathlib import Path
from datetime import datetime
import py_compile


PATCH_NAME = "death_hp_regen_hard_reset"


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

    marker = "# ✅ FINAL OVERRIDE: HARD HP REGEN TIMER RESET"

    if marker in text:
        print("ℹ️ db.py: hard HP regen reset override вже є, пропускаю.")
        return None

    backup_path = make_backup(root, target)

    override = r'''

# ==============================
# ✅ FINAL OVERRIDE: HARD HP REGEN TIMER RESET
# ==============================

def reset_hp_regen_timers_now(user_id):
    """
    Жорстко скидає всі відомі таймери HP/пасивної регенерації.

    У проєкті можуть існувати різні поля:
    - last_hp_regen_update
    - last_regen_at

    Тому оновлюємо обидва, якщо вони існують.
    """

    from datetime import datetime

    now = datetime.now().isoformat()

    try:
        init_hp_regen_system()
    except Exception:
        pass

    try:
        init_passive_regen_system()
    except Exception:
        pass

    # last_hp_regen_update
    try:
        cursor.execute("""
        UPDATE users
        SET last_hp_regen_update=?
        WHERE user_id=?
        """, (
            now,
            user_id
        ))
    except Exception:
        pass

    # last_regen_at
    try:
        cursor.execute("""
        UPDATE users
        SET last_regen_at=?
        WHERE user_id=?
        """, (
            now,
            user_id
        ))
    except Exception:
        pass

    conn.commit()


def set_current_hp(user_id, hp):
    """
    Фінальна безпечна версія встановлення HP.

    Важливо:
    після будь-якої ручної зміни HP скидаємо всі таймери регенерації,
    щоб пасивне відновлення не "наздоганяло" час бою.

    Це потрібно, щоб після смерті:
    - HP стало 1;
    - при миттєвому відкритті профілю не додавалось +19/+38 HP.
    """

    from datetime import datetime

    try:
        init_hp_regen_system()
    except Exception:
        pass

    try:
        init_passive_regen_system()
    except Exception:
        pass

    max_hp = get_max_hp(user_id)

    try:
        hp = int(hp)
    except Exception:
        hp = max_hp

    if max_hp <= 0:
        max_hp = 1

    hp = max(0, min(max_hp, hp))

    hp_full_notified = 1 if hp >= max_hp else 0
    now = datetime.now().isoformat()

    # Основний update з усіма можливими полями.
    try:
        cursor.execute("""
        UPDATE users
        SET hp=?,
            last_hp_regen_update=?,
            last_regen_at=?,
            hp_full_notified=?
        WHERE user_id=?
        """, (
            hp,
            now,
            now,
            hp_full_notified,
            user_id
        ))

        conn.commit()
        return hp

    except Exception:
        # Fallback для баз, де одного з полів може не бути.
        pass

    try:
        cursor.execute("""
        UPDATE users
        SET hp=?,
            last_hp_regen_update=?,
            hp_full_notified=?
        WHERE user_id=?
        """, (
            hp,
            now,
            hp_full_notified,
            user_id
        ))

        conn.commit()

    except Exception:
        cursor.execute("""
        UPDATE users
        SET hp=?
        WHERE user_id=?
        """, (
            hp,
            user_id
        ))

        conn.commit()

    reset_hp_regen_timers_now(user_id)

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

    # 1. Гарантуємо, що смерть ставить HP = 1.
    old_full_hp = "set_current_hp(user_id, player_max_hp)"
    new_one_hp = "set_current_hp(user_id, 1)"

    count_full_hp = text.count(old_full_hp)

    if count_full_hp > 0:
        text = text.replace(old_full_hp, new_one_hp)
        changed = True
        print(f"✅ combat.py: death full HP -> 1, замінено: {count_full_hp}")
    else:
        print("ℹ️ combat.py: full HP death рядок не знайдено, ймовірно вже HP = 1.")

    # 2. Після кожного set_current_hp(user_id, 1) у смерті примусово скидаємо таймери регену.
    reset_snippet = '''set_current_hp(user_id, 1)
            try:
                from db import reset_hp_regen_timers_now
                reset_hp_regen_timers_now(user_id)
            except Exception:
                pass'''

    if "reset_hp_regen_timers_now(user_id)" in text:
        print("ℹ️ combat.py: reset_hp_regen_timers_now вже є, пропускаю вставку.")
    else:
        death_line = "set_current_hp(user_id, 1)"
        count_death_line = text.count(death_line)

        if count_death_line <= 0:
            print("⚠️ combat.py: set_current_hp(user_id, 1) не знайдено.")
        else:
            text = text.replace(death_line, reset_snippet)
            changed = True
            print(f"✅ combat.py: додано hard reset регену після смерті, місць: {count_death_line}")

    # 3. На старті бою теж скидаємо таймер, щоб реген не накопичувався під час бою.
    start_anchor = '''        mob["player_hp"] = current_hp
        mob["player_max_hp"] = max_hp
'''

    start_insert = '''        mob["player_hp"] = current_hp
        mob["player_max_hp"] = max_hp

        # Бій почався: пасивна регенерація HP не має накопичуватись під час бою.
        try:
            from db import reset_hp_regen_timers_now
            reset_hp_regen_timers_now(user_id)
        except Exception:
            pass
'''

    if "Бій почався: пасивна регенерація HP не має накопичуватись під час бою." in text:
        print("ℹ️ combat.py: reset таймера на старті бою вже є.")
    else:
        count_anchor = text.count(start_anchor)

        if count_anchor <= 0:
            print("⚠️ combat.py: anchor старту бою не знайдено, пропускаю.")
        else:
            text = text.replace(start_anchor, start_insert, 1)
            changed = True
            print("✅ combat.py: додано hard reset регену на старті бою.")

    # 4. Оновлюємо текст смерті, якщо старий ще є.
    old_death_text = "❤️ Здоров’я відновлено\\n"
    new_death_text = "❤️ Після поразки у тебе залишилось 1 HP\\n"

    if old_death_text in text:
        text = text.replace(old_death_text, new_death_text)
        changed = True
        print("✅ combat.py: оновлено текст смерті.")
    else:
        print("ℹ️ combat.py: старий текст смерті не знайдено.")

    if changed:
        target.write_text(text, encoding="utf-8")
    else:
        print("ℹ️ combat.py: змін не внесено.")

    return backup_path


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
            "❌ Помилка компіляції після патча.\n"
            "db.py і handlers/combat.py відновлено.\n\n"
            f"{error}"
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
    print("- після смерті HP має бути 1;")
    print("- профіль одразу після смерті не має показувати +19 HP;")
    print("- пасивний реген стартує вже після бою, а не накопичується під час бою.")


if __name__ == "__main__":
    main()