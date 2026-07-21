from pathlib import Path
from datetime import datetime
import py_compile
import re
import sys

PATCH_NAME = "7_0_9_guild_exp_integration"
GUILD_SYSTEM_MARKER = "# ✅ GUILD ACTIVITY REWARDS CORE V1"
DB_MARKER = "# ✅ GUILD ACTIVITY REWARDS DB WRAPPERS V1"
REWARD_MARKER = "# ✅ GUILD ELITE MOB REWARD V1"
CONTRACT_MARKER = "# ✅ GUILD CONTRACT REWARD AUTOHOOK V1"

GUILD_SYSTEM_APPEND = r'''

# ==============================
# ✅ GUILD ACTIVITY REWARDS CORE V1
# ==============================

# 7.0.9
# Guild EXP / Resource integration points:
# - elite mob victory reward
# - contract completion reward helper

GUILD_ELITE_KILL_EXP_REWARD = 25
GUILD_ELITE_KILL_RESOURCE_REWARD = 1
GUILD_ELITE_KILL_SCORE_REASON = "Перемога над елітним мобом"

GUILD_CONTRACT_EXP_REWARD = 50
GUILD_CONTRACT_RESOURCE_REWARD = 3
GUILD_CONTRACT_SCORE_REASON = "Виконання контракту"


def _guild_activity_result_text(result):
    if not result or not result.get("success"):
        return None

    exp = int(result.get("exp", 0) or 0)
    resource = int(result.get("resource", 0) or 0)
    kills = int(result.get("kills", 0) or 0)
    contracts = int(result.get("contracts", 0) or 0)

    parts = []
    if exp:
        parts.append(f"+{exp} EXP")
    if resource:
        parts.append(f"+{resource} ресурс")
    if kills:
        parts.append(f"+{kills} вбивство")
    if contracts:
        parts.append(f"+{contracts} контракт")

    if not parts:
        return None

    return "🏰 Гільдія: " + ", ".join(parts)


def award_guild_elite_kill(user_id, mob=None):
    """
    Нарахування прогресу гільдії за перемогу над елітним мобом.

    Повертає dict add_user_guild_progress або success=False, якщо гравець без гільдії.
    """

    member = get_user_guild_member(user_id)

    if not member:
        return {
            "success": False,
            "message": "Гравець не перебуває у гільдії."
        }

    mob_name = "елітним мобом"
    try:
        if mob:
            mob_name = mob.get("name") or mob.get("title") or mob_name
    except Exception:
        pass

    return add_user_guild_progress(
        user_id=user_id,
        exp=GUILD_ELITE_KILL_EXP_REWARD,
        resource=GUILD_ELITE_KILL_RESOURCE_REWARD,
        kills=1,
        contracts=0,
        reason=f"{GUILD_ELITE_KILL_SCORE_REASON}: {mob_name}."
    )


def award_guild_contract_completion(user_id, contract=None):
    """
    Нарахування прогресу гільдії за виконання контракту.

    Цю функцію можна викликати з системи контрактів після успішного завершення контракту.
    """

    member = get_user_guild_member(user_id)

    if not member:
        return {
            "success": False,
            "message": "Гравець не перебуває у гільдії."
        }

    contract_name = "контракт"
    try:
        if isinstance(contract, dict):
            contract_name = contract.get("name") or contract.get("title") or contract.get("contract_name") or contract_name
        elif contract:
            contract_name = str(contract)
    except Exception:
        pass

    return add_user_guild_progress(
        user_id=user_id,
        exp=GUILD_CONTRACT_EXP_REWARD,
        resource=GUILD_CONTRACT_RESOURCE_REWARD,
        kills=0,
        contracts=1,
        reason=f"{GUILD_CONTRACT_SCORE_REASON}: {contract_name}."
    )


def get_guild_activity_reward_text(result):
    return _guild_activity_result_text(result)
'''

DB_APPEND = r'''

# ==============================
# ✅ GUILD ACTIVITY REWARDS DB WRAPPERS V1
# ==============================

# 7.0.9 wrappers для нарахування Guild EXP / Resource за активність.


def award_guild_elite_kill(user_id, mob=None):
    from systems.guild_system import award_guild_elite_kill as _award_guild_elite_kill
    return _award_guild_elite_kill(user_id=user_id, mob=mob)


def award_guild_contract_completion(user_id, contract=None):
    from systems.guild_system import award_guild_contract_completion as _award_guild_contract_completion
    return _award_guild_contract_completion(user_id=user_id, contract=contract)


def get_guild_activity_reward_text(result):
    from systems.guild_system import get_guild_activity_reward_text as _get_guild_activity_reward_text
    return _get_guild_activity_reward_text(result)
'''

REWARD_APPEND = r'''

# ==============================
# ✅ GUILD ELITE MOB REWARD V1
# ==============================

# 7.0.9
# Гільдія отримує прогрес за перемогу над елітним мобом.
# Hook стоїть у roll_loot(), бо roll_loot викликається після перемоги.

try:
    _base_roll_loot_before_guild_elite_reward_v1 = roll_loot
except Exception:
    _base_roll_loot_before_guild_elite_reward_v1 = None


def _guild_is_elite_mob_v1(mob):
    try:
        return bool(mob.get("is_elite", False) or mob.get("elite", False))
    except Exception:
        return False


def roll_loot(user_id, mob):
    if _base_roll_loot_before_guild_elite_reward_v1 is not None:
        messages = _base_roll_loot_before_guild_elite_reward_v1(user_id, mob)
    else:
        messages = []

    if messages is None:
        messages = []

    if _guild_is_elite_mob_v1(mob):
        try:
            from db import award_guild_elite_kill, get_guild_activity_reward_text
            result = award_guild_elite_kill(user_id, mob)
            text = get_guild_activity_reward_text(result)
            if text:
                messages.append(text)
        except Exception as error:
            print(f"⚠️ Guild elite reward failed: {error}")

    return messages
'''

CONTRACT_APPEND_TEMPLATE = r'''

# ==============================
# ✅ GUILD CONTRACT REWARD AUTOHOOK V1
# ==============================

# 7.0.9
# Auto-hook для функції {func_name}().
# Якщо функція успішно завершує контракт, гравець отримує Guild EXP/Resource.
# Hook максимально обережний: якщо не вдається визначити user_id або результат схожий на failure,
# прогрес гільдії не нараховується.

try:
    _base_{safe_name}_before_guild_contract_reward_v1 = {func_name}
except Exception:
    _base_{safe_name}_before_guild_contract_reward_v1 = None


def _guild_contract_extract_user_id_v1(args, kwargs):
    for key in ["user_id", "player_id", "telegram_id"]:
        if key in kwargs:
            return kwargs.get(key)

    if args:
        # У більшості helper-ів user_id — перший аргумент.
        try:
            return args[0]
        except Exception:
            pass

    return None


def _guild_contract_result_looks_success_v1(result):
    if result is None:
        # Багато legacy-функцій нічого не повертають після успішного update.
        return True

    if isinstance(result, dict):
        if result.get("success") is False:
            return False
        if result.get("ok") is False:
            return False
        if result.get("status") in ["failed", "error", "rejected"]:
            return False
        return True

    if result is False:
        return False

    return True


def {func_name}(*args, **kwargs):
    result = _base_{safe_name}_before_guild_contract_reward_v1(*args, **kwargs)

    try:
        if not _guild_contract_result_looks_success_v1(result):
            return result

        user_id = _guild_contract_extract_user_id_v1(args, kwargs)
        if not user_id:
            return result

        from db import award_guild_contract_completion
        award_guild_contract_completion(user_id, contract="контракт")
    except Exception as error:
        print(f"⚠️ Guild contract reward failed in {func_name}: {{error}}")

    return result
'''

CANDIDATE_FUNC_RE = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.M)


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def append_if_missing(root, target, marker, code):
    original = target.read_text(encoding="utf-8")
    if marker in original:
        return None, original, False
    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + code + "\n", encoding="utf-8")
    return backup, original, True


def patch_guild_system(root):
    target = root / "systems" / "guild_system.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено systems/guild_system.py")
    return target, *append_if_missing(root, target, "# ✅ GUILD ACTIVITY REWARDS CORE V1", GUILD_SYSTEM_APPEND)


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")
    return target, *append_if_missing(root, target, "# ✅ GUILD ACTIVITY REWARDS DB WRAPPERS V1", DB_APPEND)


def patch_reward_system(root):
    target = root / "systems" / "reward_system.py"
    if not target.exists():
        print("⚠️ systems/reward_system.py не знайдено. Elite mob reward hook пропущено.")
        return target, None, "", False
    return target, *append_if_missing(root, target, "# ✅ GUILD ELITE MOB REWARD V1", REWARD_APPEND)


def find_contract_candidates(root):
    candidates = []
    for folder in [root / "systems", root / "handlers"]:
        if not folder.exists():
            continue
        for path in folder.glob("*.py"):
            if path.name in ["guild_system.py"]:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            low = text.lower()
            if "contract" not in low and "контракт" not in low:
                continue
            if CONTRACT_MARKER in text:
                continue
            for match in CANDIDATE_FUNC_RE.finditer(text):
                name = match.group(1)
                lname = name.lower()
                if "contract" not in lname:
                    continue
                if any(word in lname for word in ["complete", "finish", "claim", "turn_in", "done", "reward"]):
                    candidates.append((path, name))
    return candidates


def patch_contract_hooks(root):
    candidates = find_contract_candidates(root)
    changed = []
    backups = []
    originals = []

    if not candidates:
        return changed, backups, originals, []

    # Avoid patching too many. Patch the first candidate per file, prefer handlers over systems by sort.
    by_file = {}
    for path, name in candidates:
        by_file.setdefault(path, []).append(name)

    for path, names in by_file.items():
        original = path.read_text(encoding="utf-8")
        code_parts = []
        for name in names[:2]:
            safe_name = re.sub(r"[^A-Za-z0-9_]", "_", name)
            code_parts.append(CONTRACT_APPEND_TEMPLATE.format(func_name=name, safe_name=safe_name))
        backup = make_backup(root, path)
        path.write_text(original.rstrip() + "\n" + "\n".join(code_parts) + "\n", encoding="utf-8")
        changed.append(path)
        backups.append(backup)
        originals.append((path, original))

    return changed, backups, originals, candidates


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []
    contract_candidates = []

    try:
        for patch_func in [patch_guild_system, patch_db, patch_reward_system]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        c_changed, c_backups, c_originals, contract_candidates = patch_contract_hooks(root)
        changed_files.extend(c_changed)
        backups.extend(c_backups)
        originals.extend(c_originals)

        unique_files = []
        for file_path in changed_files:
            if file_path and file_path not in unique_files and file_path.exists():
                unique_files.append(file_path)

        for file_path in unique_files:
            py_compile.compile(str(file_path), doraise=True)

        sys.path.insert(0, str(root))
        from db import init_guild_system
        init_guild_system()

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_7_0_9_guild_exp_integration.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.9 Guild EXP integration застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files if p)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- за перемогу над елітним мобом: +25 Guild EXP, +1 Guild Resource, +1 guild kill")
    print("- helper award_guild_contract_completion(): +50 Guild EXP, +3 Guild Resource, +1 guild contract")
    print("- add_user_guild_progress() залишається центральною точкою прогресу")
    print("- повідомлення в луті для елітного моба: 🏰 Гільдія: +25 EXP, +1 ресурс, +1 вбивство")

    if contract_candidates:
        print("\nAuto-hook для контрактів знайдено:")
        for path, name in contract_candidates:
            print(f"- {path}: {name}()")
    else:
        print("\n⚠️ Auto-hook для контрактів не знайдено автоматично.")
        print("Контрактний helper додано, але для точного підключення надішли файл системи контрактів/handlers, де завершується контракт.")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\guild_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\systems\\reward_system.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
