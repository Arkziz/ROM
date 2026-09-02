import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

def _positive_int_env(name, default):
    raw = str(os.getenv(name, default)).strip()
    value = int(raw)
    if value <= 0:
        raise RuntimeError(f"{name} має бути додатним цілим числом")
    return value

def _admin_ids_env():
    raw = str(os.getenv("ROM_ADMIN_USER_IDS", "")).strip()
    return frozenset(int(part.strip()) for part in raw.split(",") if part.strip())

ROM_ADMIN_USER_IDS = _admin_ids_env()
ROM_ADMIN_CRYSTAL_CREDIT_MAX = _positive_int_env("ROM_ADMIN_CRYSTAL_CREDIT_MAX", "10000")
ROM_ADMIN_CRYSTAL_DEBIT_MAX = _positive_int_env("ROM_ADMIN_CRYSTAL_DEBIT_MAX", "10000")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не знайдено у .env")