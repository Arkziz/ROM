from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_12_auction_expiration_cleanup"
SYSTEM_TARGET = Path("systems") / "auction_house_system.py"
DB_TARGET = Path("db.py")
HANDLER_TARGET = Path("handlers") / "auction_house.py"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE EXPIRATION CLEANUP V2"
DB_MARKER = "# ✅ AUCTION HOUSE EXPIRATION CLEANUP WRAPPERS V2"
HANDLER_MARKER = "# ✅ AUCTION HOUSE EXPIRATION CLEANUP UI V2"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE EXPIRATION CLEANUP V2
# ==============================

AUCTION_ACTIVE_DAYS_V2 = 7
AUCTION_UNCLAIMED_RETENTION_DAYS_V2 = 30


def _auction_now_iso_v2():
    from datetime import datetime
    return datetime.now().isoformat()


def _auction_parse_dt_v2(value):
    from datetime import datetime

    value = str(value or "").strip()
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except Exception:
        pass

    try:
        return datetime.fromisoformat(value.replace("T", " ").split(".")[0])
    except Exception:
        return None


def _auction_plus_days_iso_v2(base_iso=None, days=30):
    from datetime import datetime, timedelta

    base_dt = _auction_parse_dt_v2(base_iso) or datetime.now()
    return (base_dt + timedelta(days=int(days))).isoformat()


def _auction_column_exists_v2(table_name, column_name):
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return column_name in {row[1] for row in cursor.fetchall()}
    except Exception:
        return False


def _auction_safe_status_v2(name, fallback):
    return globals().get(name, fallback)


AUCTION_STATUS_ACTIVE_V2 = _auction_safe_status_v2("AUCTION_STATUS_ACTIVE", "ACTIVE")
AUCTION_STATUS_SOLD_UNCLAIMED_V2 = _auction_safe_status_v2("AUCTION_STATUS_SOLD_UNCLAIMED", "SOLD_UNCLAIMED")
AUCTION_STATUS_SOLD_CLAIMED_V2 = _auction_safe_status_v2("AUCTION_STATUS_SOLD_CLAIMED", "SOLD_CLAIMED")
AUCTION_STATUS_EXPIRED_UNCLAIMED_V2 = _auction_safe_status_v2("AUCTION_STATUS_EXPIRED_UNCLAIMED", "EXPIRED_UNCLAIMED")
AUCTION_STATUS_EXPIRED_CLAIMED_V2 = _auction_safe_status_v2("AUCTION_STATUS_EXPIRED_CLAIMED", "EXPIRED_CLAIMED")
AUCTION_STATUS_DELETED_V2 = _auction_safe_status_v2("AUCTION_STATUS_DELETED", "DELETED")


try:
    _auction_base_update_expired_auction_lots_before_cleanup_v2 = update_expired_auction_lots
except NameError:
    _auction_base_update_expired_auction_lots_before_cleanup_v2 = None


def update_expired_auction_lots(now_iso=None):
    """
    Повний cleanup Торгового Дому.

    Правила:
    - ACTIVE із expires_at <= now -> EXPIRED_UNCLAIMED;
    - EXPIRED_UNCLAIMED із delete_after <= now -> DELETED;
    - SOLD_UNCLAIMED із delete_after <= now -> DELETED.

    SOLD_CLAIMED / EXPIRED_CLAIMED не видаляються цим cleanup-ом, бо це історія.
    """

    init_auction_house()

    from datetime import datetime

    now_iso = now_iso or _auction_now_iso_v2()
    now_dt = _auction_parse_dt_v2(now_iso) or datetime.now()

    result = {
        "success": True,
        "now": now_iso,
        "expired_active": 0,
        "deleted_expired_unclaimed": 0,
        "deleted_sold_unclaimed": 0,
        "fixed_missing_delete_after": 0,
    }

    has_delete_after = _auction_column_exists_v2("auction_lots", "delete_after")
    has_expires_at = _auction_column_exists_v2("auction_lots", "expires_at")
    has_updated_at = _auction_column_exists_v2("auction_lots", "updated_at")

    if not has_expires_at:
        return result

    # 1. ACTIVE -> EXPIRED_UNCLAIMED
    cursor.execute("""
    SELECT id, expires_at, delete_after
    FROM auction_lots
    WHERE status=?
    """, (AUCTION_STATUS_ACTIVE_V2,))
    active_rows = cursor.fetchall()

    for row in active_rows:
        expires_dt = _auction_parse_dt_v2(row["expires_at"])
        if not expires_dt or expires_dt > now_dt:
            continue

        delete_after = row["delete_after"] if has_delete_after else None
        if not delete_after:
            delete_after = _auction_plus_days_iso_v2(now_iso, AUCTION_UNCLAIMED_RETENTION_DAYS_V2)

        if has_delete_after and has_updated_at:
            cursor.execute("""
            UPDATE auction_lots
            SET status=?, delete_after=?, updated_at=?
            WHERE id=? AND status=?
            """, (
                AUCTION_STATUS_EXPIRED_UNCLAIMED_V2,
                delete_after,
                now_iso,
                row["id"],
                AUCTION_STATUS_ACTIVE_V2,
            ))
        elif has_delete_after:
            cursor.execute("""
            UPDATE auction_lots
            SET status=?, delete_after=?
            WHERE id=? AND status=?
            """, (
                AUCTION_STATUS_EXPIRED_UNCLAIMED_V2,
                delete_after,
                row["id"],
                AUCTION_STATUS_ACTIVE_V2,
            ))
        else:
            cursor.execute("""
            UPDATE auction_lots
            SET status=?
            WHERE id=? AND status=?
            """, (
                AUCTION_STATUS_EXPIRED_UNCLAIMED_V2,
                row["id"],
                AUCTION_STATUS_ACTIVE_V2,
            ))

        if cursor.rowcount:
            result["expired_active"] += 1

    # 2. Fix missing delete_after for unclaimed statuses.
    if has_delete_after:
        cursor.execute("""
        SELECT id, status, sold_at, expires_at, created_at, delete_after
        FROM auction_lots
        WHERE status IN (?, ?)
          AND (delete_after IS NULL OR delete_after='')
        """, (
            AUCTION_STATUS_EXPIRED_UNCLAIMED_V2,
            AUCTION_STATUS_SOLD_UNCLAIMED_V2,
        ))
        missing_rows = cursor.fetchall()

        for row in missing_rows:
            base_date = row["sold_at"] or row["expires_at"] or row["created_at"] or now_iso
            delete_after = _auction_plus_days_iso_v2(base_date, AUCTION_UNCLAIMED_RETENTION_DAYS_V2)
            cursor.execute("""
            UPDATE auction_lots
            SET delete_after=?
            WHERE id=?
            """, (delete_after, row["id"]))
            if cursor.rowcount:
                result["fixed_missing_delete_after"] += 1

    # 3. EXPIRED_UNCLAIMED -> DELETED after retention.
    if has_delete_after:
        cursor.execute("""
        SELECT id, delete_after
        FROM auction_lots
        WHERE status=?
          AND delete_after IS NOT NULL
          AND delete_after<>''
        """, (AUCTION_STATUS_EXPIRED_UNCLAIMED_V2,))
        expired_unclaimed_rows = cursor.fetchall()

        for row in expired_unclaimed_rows:
            delete_dt = _auction_parse_dt_v2(row["delete_after"])
            if not delete_dt or delete_dt > now_dt:
                continue

            if has_updated_at:
                cursor.execute("""
                UPDATE auction_lots
                SET status=?, updated_at=?
                WHERE id=? AND status=?
                """, (
                    AUCTION_STATUS_DELETED_V2,
                    now_iso,
                    row["id"],
                    AUCTION_STATUS_EXPIRED_UNCLAIMED_V2,
                ))
            else:
                cursor.execute("""
                UPDATE auction_lots
                SET status=?
                WHERE id=? AND status=?
                """, (
                    AUCTION_STATUS_DELETED_V2,
                    row["id"],
                    AUCTION_STATUS_EXPIRED_UNCLAIMED_V2,
                ))

            if cursor.rowcount:
                result["deleted_expired_unclaimed"] += 1

        # 4. SOLD_UNCLAIMED -> DELETED after retention.
        cursor.execute("""
        SELECT id, delete_after
        FROM auction_lots
        WHERE status=?
          AND delete_after IS NOT NULL
          AND delete_after<>''
        """, (AUCTION_STATUS_SOLD_UNCLAIMED_V2,))
        sold_unclaimed_rows = cursor.fetchall()

        for row in sold_unclaimed_rows:
            delete_dt = _auction_parse_dt_v2(row["delete_after"])
            if not delete_dt or delete_dt > now_dt:
                continue

            if has_updated_at:
                cursor.execute("""
                UPDATE auction_lots
                SET status=?, updated_at=?
                WHERE id=? AND status=?
                """, (
                    AUCTION_STATUS_DELETED_V2,
                    now_iso,
                    row["id"],
                    AUCTION_STATUS_SOLD_UNCLAIMED_V2,
                ))
            else:
                cursor.execute("""
                UPDATE auction_lots
                SET status=?
                WHERE id=? AND status=?
                """, (
                    AUCTION_STATUS_DELETED_V2,
                    row["id"],
                    AUCTION_STATUS_SOLD_UNCLAIMED_V2,
                ))

            if cursor.rowcount:
                result["deleted_sold_unclaimed"] += 1

    conn.commit()
    return result


def get_auction_cleanup_report():
    """Повертає агреговану статистику статусів лотів."""

    init_auction_house()
    update_expired_auction_lots()

    cursor.execute("""
    SELECT status, COUNT(*) AS count
    FROM auction_lots
    GROUP BY status
    ORDER BY status
    """)
    rows = cursor.fetchall()

    status_counts = {}
    for row in rows:
        status_counts[row["status"]] = int(row["count"] or 0)

    result = {
        "success": True,
        "status_counts": status_counts,
        "active": status_counts.get(AUCTION_STATUS_ACTIVE_V2, 0),
        "sold_unclaimed": status_counts.get(AUCTION_STATUS_SOLD_UNCLAIMED_V2, 0),
        "sold_claimed": status_counts.get(AUCTION_STATUS_SOLD_CLAIMED_V2, 0),
        "expired_unclaimed": status_counts.get(AUCTION_STATUS_EXPIRED_UNCLAIMED_V2, 0),
        "expired_claimed": status_counts.get(AUCTION_STATUS_EXPIRED_CLAIMED_V2, 0),
        "deleted": status_counts.get(AUCTION_STATUS_DELETED_V2, 0),
    }

    return result
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE EXPIRATION CLEANUP WRAPPERS V2
# ==============================


def update_expired_auction_lots(now_iso=None):
    from systems.auction_house_system import update_expired_auction_lots as _func
    return _func(now_iso=now_iso)


def get_auction_cleanup_report():
    from systems.auction_house_system import get_auction_cleanup_report as _func
    return _func()


def init_auction_house():
    """
    Wrapper initialization.
    Also runs lightweight cleanup so expiration is processed after bot start
    and whenever Auction House systems initialize.
    """

    from systems.auction_house_system import init_auction_house as _init
    from systems.auction_house_system import update_expired_auction_lots as _cleanup

    _init()
    try:
        _cleanup()
    except Exception:
        pass

    return True
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE EXPIRATION CLEANUP UI V2
# ==============================


def build_auction_cleanup_report_text_v2(result=None):
    if result is None:
        from db import get_auction_cleanup_report
        result = get_auction_cleanup_report()

    counts = result.get("status_counts", {}) if isinstance(result, dict) else {}

    return (
        "🧹 Auction cleanup / Торговий Дім\n\n"
        f"ACTIVE: {counts.get('ACTIVE', 0)}\n"
        f"SOLD_UNCLAIMED: {counts.get('SOLD_UNCLAIMED', 0)}\n"
        f"SOLD_CLAIMED: {counts.get('SOLD_CLAIMED', 0)}\n"
        f"EXPIRED_UNCLAIMED: {counts.get('EXPIRED_UNCLAIMED', 0)}\n"
        f"EXPIRED_CLAIMED: {counts.get('EXPIRED_CLAIMED', 0)}\n"
        f"DELETED: {counts.get('DELETED', 0)}"
    )


try:
    _auction_base_build_auction_house_text_before_cleanup_v2 = build_auction_house_text
except NameError:
    _auction_base_build_auction_house_text_before_cleanup_v2 = None


def build_auction_house_text(user_id):
    """Override: cleanup runs whenever player opens Auction House."""

    try:
        from db import update_expired_auction_lots
        update_expired_auction_lots()
    except Exception:
        pass

    if _auction_base_build_auction_house_text_before_cleanup_v2:
        return _auction_base_build_auction_house_text_before_cleanup_v2(user_id)

    return (
        "🏛️ Торговий дім\n\n"
        "Тут гравці можуть виставляти товари, купувати лоти та забирати завершені продажі."
    )


def _auction_register_expiration_cleanup_handlers_v2(bot):

    @bot.message_handler(commands=["auction_cleanup"])
    def auction_cleanup_command_v2(message):
        from db import update_expired_auction_lots, get_auction_cleanup_report

        cleanup = update_expired_auction_lots()
        report = get_auction_cleanup_report()

        text = (
            "🧹 Cleanup виконано.\n\n"
            f"ACTIVE → EXPIRED_UNCLAIMED: {cleanup.get('expired_active', 0)}\n"
            f"EXPIRED_UNCLAIMED → DELETED: {cleanup.get('deleted_expired_unclaimed', 0)}\n"
            f"SOLD_UNCLAIMED → DELETED: {cleanup.get('deleted_sold_unclaimed', 0)}\n"
            f"Виправлено delete_after: {cleanup.get('fixed_missing_delete_after', 0)}\n\n"
            f"{build_auction_cleanup_report_text_v2(report)}"
        )

        bot.send_message(message.chat.id, text)

    @bot.message_handler(commands=["auction_debug"])
    def auction_debug_command_v2(message):
        from db import get_auction_cleanup_report
        bot.send_message(message.chat.id, build_auction_cleanup_report_text_v2(get_auction_cleanup_report()))


try:
    _auction_base_register_handlers_before_expiration_cleanup_v2 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_expiration_cleanup_v2 = None


def register_auction_house_handlers(bot):
    _auction_register_expiration_cleanup_handlers_v2(bot)

    if _auction_base_register_handlers_before_expiration_cleanup_v2:
        _auction_base_register_handlers_before_expiration_cleanup_v2(bot)
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def append_once(root, rel_path, marker, append_code):
    target = root / rel_path
    if not target.exists():
        raise SystemExit(f"❌ Не знайдено {rel_path}")

    original = target.read_text(encoding="utf-8")
    if marker in original:
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + append_code + "\n", encoding="utf-8")
    return target, backup, original, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        patches = [
            (SYSTEM_TARGET, SYSTEM_MARKER, SYSTEM_APPEND),
            (DB_TARGET, DB_MARKER, DB_APPEND),
            (HANDLER_TARGET, HANDLER_MARKER, HANDLER_APPEND),
        ]

        for rel_path, marker, append_code in patches:
            file_path, backup, original, changed = append_once(root, rel_path, marker, append_code)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        for rel_path in [SYSTEM_TARGET, DB_TARGET, HANDLER_TARGET]:
            py_compile.compile(str(root / rel_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_8_0_12_auction_expiration_cleanup.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.12 Auction Expiration Cleanup застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- ACTIVE лоти після expires_at переходять у EXPIRED_UNCLAIMED")
    print("- EXPIRED_UNCLAIMED після delete_after переходять у DELETED")
    print("- SOLD_UNCLAIMED після delete_after переходять у DELETED")
    print("- відсутній delete_after автоматично проставляється")
    print("- cleanup запускається при відкритті Торгового Дому")
    print("- cleanup запускається через wrapper init_auction_house()")
    print("- /auction_cleanup")
    print("- /auction_debug")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
