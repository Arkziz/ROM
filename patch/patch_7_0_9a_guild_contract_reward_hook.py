from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "7_0_9a_guild_contract_reward_hook"
TARGET_RELATIVE_PATH = Path("db.py")
MARKER = "# ✅ GUILD CONTRACT REWARD CLAIM HOOK V1"

APPEND_CODE = r'''

# ==============================
# ✅ GUILD CONTRACT REWARD CLAIM HOOK V1
# ==============================

# 7.0.9a
# Точний hook для поточної системи контрактів у db.py.
# Контракт здається через claim_contract_reward(user_id), тому Guild EXP/Resource
# треба нараховувати саме після успішної здачі контракту.
#
# Нагорода гільдії:
# - +50 Guild EXP
# - +3 Guild Resource
# - +1 guild contract

try:
    _base_claim_contract_reward_before_guild_reward_v1 = claim_contract_reward
except Exception:
    _base_claim_contract_reward_before_guild_reward_v1 = None


def _guild_contract_reward_result_success_v1(result):
    if not result:
        return False

    if isinstance(result, dict):
        if result.get("success") is False:
            return False

        message = str(result.get("message", ""))

        if "🎁 Контракт здано" in message:
            return True

        if "Контракт здано" in message:
            return True

        return False

    return False


def _guild_contract_reward_append_message_v1(result, guild_result):
    try:
        guild_text = get_guild_activity_reward_text(guild_result)
    except Exception:
        guild_text = None

    if not guild_text:
        return result

    if isinstance(result, dict):
        message = str(result.get("message", ""))
        if guild_text not in message:
            result = dict(result)
            result["message"] = message.rstrip() + "\n" + guild_text
        return result

    return result


def claim_contract_reward(user_id):
    """
    FINAL OVERRIDE:
    Здача контракту + Guild reward.
    """

    if _base_claim_contract_reward_before_guild_reward_v1 is None:
        return {
            "success": False,
            "message": "❌ Функція здачі контракту недоступна."
        }

    # Зберігаємо active_contract ДО базової здачі, бо базова функція після нагороди
    # видаляє контракт із user_active_contracts.
    try:
        active_contract_before_claim = get_active_contract(user_id)
    except Exception:
        active_contract_before_claim = None

    result = _base_claim_contract_reward_before_guild_reward_v1(user_id)

    if not _guild_contract_reward_result_success_v1(result):
        return result

    # Захист від випадкового нарахування, якщо до здачі контракту не було або він не completed.
    if not active_contract_before_claim:
        return result

    try:
        if not active_contract_before_claim.get("completed"):
            return result
        if active_contract_before_claim.get("reward_claimed"):
            return result
    except Exception:
        return result

    try:
        contract_name = active_contract_before_claim.get("target_mob_name") or "контракт"
        guild_result = award_guild_contract_completion(user_id, contract=contract_name)
        result = _guild_contract_reward_append_message_v1(result, guild_result)
    except Exception as error:
        print(f"⚠️ Guild contract reward hook failed: {error}")

    return result
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ GUILD CONTRACT REWARD CLAIM HOOK V1 уже застосований, пропускаю.")
        return

    if "def claim_contract_reward" not in original:
        raise SystemExit("❌ У db.py не знайдено def claim_contract_reward(user_id)")

    if "award_guild_contract_completion" not in original:
        raise SystemExit(
            "❌ У db.py не знайдено award_guild_contract_completion().\n"
            "Спочатку застосуй patch_7_0_9_guild_exp_integration.py"
        )

    backup_path = make_backup(root, target)
    updated = original.rstrip() + "\n" + APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_9a_guild_contract_reward_hook.\n"
            "db.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.9a Guild Contract Reward Hook застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ db.py пройшов py_compile.")
    print("")
    print("Що додано:")
    print("- після успішної здачі контракту нараховується Guild progress")
    print("- +50 Guild EXP")
    print("- +3 Guild Resource")
    print("- +1 guild contract")
    print("- у повідомлення здачі додається рядок: 🏰 Гільдія: +50 EXP, +3 ресурс, +1 контракт")
    print("- повторне нарахування за той самий контракт не має відбутися, бо контракт видаляється після здачі")
    print("")
    print("Після патча:")
    print("python -m py_compile .\\db.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
