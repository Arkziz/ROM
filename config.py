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

# ROM Stage 18.5.1: validated, fail-closed external links.
from urllib.parse import urlsplit as _urlsplit

_GAME_CHAT_URL_RAW = str(os.getenv("GAME_CHAT_URL", "") or "").strip()
_NEWS_CHANNEL_URL_RAW = str(os.getenv("NEWS_CHANNEL_URL", "") or "").strip()
_SUPPORT_URL_RAW = str(os.getenv("SUPPORT_URL", "") or "").strip()


def _validated_external_https_url(value, allowed_hosts):
    value = str(value or "").strip()
    if not value or len(value) > 2048:
        return None
    try:
        parsed = _urlsplit(value)
    except Exception:
        return None
    host = str(parsed.hostname or "").casefold()
    allowed = {str(item).casefold() for item in allowed_hosts}
    if (
        parsed.scheme.casefold() != "https"
        or not host
        or host not in allowed
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        return None
    return value


GAME_CHAT_URL = _validated_external_https_url(
    _GAME_CHAT_URL_RAW, {"t.me", "telegram.me"}
)
NEWS_CHANNEL_URL = _validated_external_https_url(
    _NEWS_CHANNEL_URL_RAW, {"t.me", "telegram.me"}
)
SUPPORT_URL = _validated_external_https_url(
    _SUPPORT_URL_RAW, {"send.monobank.ua"}
)


def get_external_links_config():
    """Return only validated URLs; invalid or empty values stay disabled."""
    return {
        "game_chat": GAME_CHAT_URL,
        "news_channel": NEWS_CHANNEL_URL,
        "support": SUPPORT_URL,
    }

