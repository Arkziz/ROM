import time
import threading

from db import (
    get_users_for_energy_full_notification,
    get_users_for_hp_full_notification
)


# ==============================
# ✅ NOTIFICATION CONFIG
# ==============================

NOTIFICATION_CHECK_INTERVAL_SECONDS = 60


# ==============================
# 🔋 ENERGY NOTIFICATIONS
# ==============================

def notify_energy_full(bot_instance):
    users = get_users_for_energy_full_notification()

    for user_id in users:
        try:
            bot_instance.send_message(
                user_id,
                (
                    "🔋 Енергія повністю відновлена!\n\n"
                    "Ти знову маєш повний запас енергії.\n"
                    "Можна вирушати на полювання."
                )
            )
        except Exception as send_error:
            print(f"⚠️ Не вдалося надіслати energy notification {user_id}: {send_error}")


# ==============================
# ❤️ HP NOTIFICATIONS
# ==============================

def notify_hp_restored(bot_instance):
    users = get_users_for_hp_full_notification()

    for user_id in users:
        try:
            bot_instance.send_message(
                user_id,
                (
                    "❤️ Здоров’я повністю відновлено!\n\n"
                    "Персонаж готовий до нового полювання."
                )
            )
        except Exception as send_error:
            print(f"⚠️ Не вдалося надіслати HP notification {user_id}: {send_error}")


# ==============================
# 📜 FUTURE CONTRACT NOTIFICATIONS
# ==============================

def notify_daily_contracts_reset(bot_instance):
    pass


# ==============================
# ⚒️ FUTURE CRAFT / REPAIR NOTIFICATIONS
# ==============================

def notify_craft_or_repair_ready(bot_instance):
    pass


# ==============================
# ✅ MAIN NOTIFICATION WORKER
# ==============================

def notification_worker(bot_instance):
    while True:
        try:
            notify_energy_full(bot_instance)
            notify_hp_restored(bot_instance)

            # Майбутні повідомлення:
            # notify_daily_contracts_reset(bot_instance)
            # notify_craft_or_repair_ready(bot_instance)

        except Exception as error:
            print(f"⚠️ NOTIFICATION WORKER ERROR: {error}")

        time.sleep(NOTIFICATION_CHECK_INTERVAL_SECONDS)


def start_notification_worker(bot_instance):
    thread = threading.Thread(
        target=notification_worker,
        args=(bot_instance,),
        daemon=True
    )

    thread.start()

    print("✅ NOTIFICATION WORKER STARTED")