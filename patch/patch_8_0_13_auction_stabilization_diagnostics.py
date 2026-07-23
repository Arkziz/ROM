from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_13_auction_stabilization_diagnostics"
SYSTEM_TARGET = Path("systems") / "auction_house_system.py"
DB_TARGET = Path("db.py")
HANDLER_TARGET = Path("handlers") / "auction_house.py"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE STABILIZATION DIAGNOSTICS V1"
DB_MARKER = "# ✅ AUCTION HOUSE STABILIZATION DIAGNOSTICS WRAPPERS V1"
HANDLER_MARKER = "# ✅ AUCTION HOUSE STABILIZATION DIAGNOSTICS UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE STABILIZATION DIAGNOSTICS V1
# ==============================


def _auction_diag_parse_decimal_v1(value):
    from decimal import Decimal, InvalidOperation

    try:
        return Decimal(str(value))
    except Exception:
        return None


def _auction_diag_column_exists_v1(table_name, column_name):
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return column_name in {row[1] for row in cursor.fetchall()}
    except Exception:
        return False


def _auction_diag_table_exists_v1(table_name):
    try:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None
    except Exception:
        return False


def _auction_diag_statuses_v1():
    return {
        "ACTIVE": globals().get("AUCTION_STATUS_ACTIVE", "ACTIVE"),
        "SOLD_UNCLAIMED": globals().get("AUCTION_STATUS_SOLD_UNCLAIMED", "SOLD_UNCLAIMED"),
        "SOLD_CLAIMED": globals().get("AUCTION_STATUS_SOLD_CLAIMED", "SOLD_CLAIMED"),
        "EXPIRED_UNCLAIMED": globals().get("AUCTION_STATUS_EXPIRED_UNCLAIMED", "EXPIRED_UNCLAIMED"),
        "EXPIRED_CLAIMED": globals().get("AUCTION_STATUS_EXPIRED_CLAIMED", "EXPIRED_CLAIMED"),
        "DELETED": globals().get("AUCTION_STATUS_DELETED", "DELETED"),
    }


def _auction_diag_price_limits_v1():
    from decimal import Decimal

    min_price = globals().get("AUCTION_MIN_PRICE", Decimal("1.0"))
    max_price = globals().get("AUCTION_MAX_PRICE", Decimal("999999.0"))

    return Decimal(str(min_price)), Decimal(str(max_price))


def get_auction_diagnostics_report():
    """
    Conservative diagnostics for Auction House.
    Does not mutate state except running regular expiration cleanup.
    """

    init_auction_house()

    try:
        update_expired_auction_lots()
    except Exception:
        pass

    statuses = _auction_diag_statuses_v1()
    min_price, max_price = _auction_diag_price_limits_v1()

    result = {
        "success": True,
        "status_counts": {},
        "total_lots": 0,
        "bad_price_lots": [],
        "missing_snapshot_lots": [],
        "active_missing_expires_at": [],
        "unclaimed_missing_delete_after": [],
        "sold_unclaimed_without_buyer": [],
        "active_lots_by_seller": [],
        "max_active_lots_per_seller": 20,
        "tables_ok": True,
        "missing_tables": [],
    }

    required_tables = ["auction_lots", "auction_history"]
    for table_name in required_tables:
        if not _auction_diag_table_exists_v1(table_name):
            result["tables_ok"] = False
            result["missing_tables"].append(table_name)

    if not result["tables_ok"]:
        return result

    cursor.execute("SELECT COUNT(*) AS count FROM auction_lots")
    row = cursor.fetchone()
    result["total_lots"] = int(row["count"] or 0) if row else 0

    cursor.execute("""
    SELECT status, COUNT(*) AS count
    FROM auction_lots
    GROUP BY status
    ORDER BY status
    """)
    for row in cursor.fetchall():
        result["status_counts"][row["status"]] = int(row["count"] or 0)

    cursor.execute("""
    SELECT id, seller_user_id, item_name, price, status, item_snapshot_json, expires_at, delete_after, buyer_user_id
    FROM auction_lots
    ORDER BY id DESC
    """)
    rows = cursor.fetchall()

    for row in rows:
        lot_id = row["id"]
        status = row["status"]
        price = _auction_diag_parse_decimal_v1(row["price"])

        if price is None or price < min_price or price > max_price:
            result["bad_price_lots"].append(lot_id)

        if not str(row["item_snapshot_json"] or "").strip():
            result["missing_snapshot_lots"].append(lot_id)

        if status == statuses["ACTIVE"] and not str(row["expires_at"] or "").strip():
            result["active_missing_expires_at"].append(lot_id)

        if status in (statuses["SOLD_UNCLAIMED"], statuses["EXPIRED_UNCLAIMED"]):
            if not str(row["delete_after"] or "").strip():
                result["unclaimed_missing_delete_after"].append(lot_id)

        if status == statuses["SOLD_UNCLAIMED"] and not row["buyer_user_id"]:
            result["sold_unclaimed_without_buyer"].append(lot_id)

    cursor.execute("""
    SELECT seller_user_id, COUNT(*) AS active_count
    FROM auction_lots
    WHERE status=?
    GROUP BY seller_user_id
    ORDER BY active_count DESC
    """, (statuses["ACTIVE"],))
    result["active_lots_by_seller"] = [
        {
            "seller_user_id": row["seller_user_id"],
            "active_count": int(row["active_count"] or 0),
        }
        for row in cursor.fetchall()
    ]

    return result


def run_auction_sanity_fix():
    """
    Conservative repair:
    - runs expiration cleanup;
    - fills missing delete_after for unclaimed lots through cleanup;
    - does not delete or modify sold/claimed historical data;
    - does not attempt to reconstruct broken snapshots.
    """

    init_auction_house()

    before = get_auction_diagnostics_report()
    cleanup = update_expired_auction_lots()
    after = get_auction_diagnostics_report()

    return {
        "success": True,
        "cleanup": cleanup,
        "before": before,
        "after": after,
    }
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE STABILIZATION DIAGNOSTICS WRAPPERS V1
# ==============================


def get_auction_diagnostics_report():
    from systems.auction_house_system import get_auction_diagnostics_report as _func
    return _func()


def run_auction_sanity_fix():
    from systems.auction_house_system import run_auction_sanity_fix as _func
    return _func()
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE STABILIZATION DIAGNOSTICS UI V1
# ==============================


def _auction_list_short_v1(values, limit=10):
    values = list(values or [])
    if not values:
        return "немає"

    shown = values[:limit]
    text = ", ".join(str(x) for x in shown)
    if len(values) > limit:
        text += f" ... +{len(values) - limit}"
    return text


def build_auction_diagnostics_text_v1(report):
    counts = report.get("status_counts", {}) if isinstance(report, dict) else {}
    active_by_seller = report.get("active_lots_by_seller", []) if isinstance(report, dict) else []

    top_sellers = []
    for row in active_by_seller[:5]:
        top_sellers.append(f"{row.get('seller_user_id')}: {row.get('active_count')}")

    if not top_sellers:
        top_sellers_text = "немає"
    else:
        top_sellers_text = "\n".join(f"• {x}" for x in top_sellers)

    return (
        "🧪 Auction diagnostics\n\n"
        f"Таблиці OK: {'так' if report.get('tables_ok') else 'ні'}\n"
        f"Всього лотів: {report.get('total_lots', 0)}\n\n"
        "Статуси:\n"
        f"• ACTIVE: {counts.get('ACTIVE', 0)}\n"
        f"• SOLD_UNCLAIMED: {counts.get('SOLD_UNCLAIMED', 0)}\n"
        f"• SOLD_CLAIMED: {counts.get('SOLD_CLAIMED', 0)}\n"
        f"• EXPIRED_UNCLAIMED: {counts.get('EXPIRED_UNCLAIMED', 0)}\n"
        f"• EXPIRED_CLAIMED: {counts.get('EXPIRED_CLAIMED', 0)}\n"
        f"• DELETED: {counts.get('DELETED', 0)}\n\n"
        "Потенційні проблеми:\n"
        f"• Некоректна ціна: {_auction_list_short_v1(report.get('bad_price_lots'))}\n"
        f"• Немає snapshot: {_auction_list_short_v1(report.get('missing_snapshot_lots'))}\n"
        f"• ACTIVE без expires_at: {_auction_list_short_v1(report.get('active_missing_expires_at'))}\n"
        f"• Unclaimed без delete_after: {_auction_list_short_v1(report.get('unclaimed_missing_delete_after'))}\n"
        f"• SOLD_UNCLAIMED без buyer: {_auction_list_short_v1(report.get('sold_unclaimed_without_buyer'))}\n\n"
        "Активні лоти за продавцями TOP-5:\n"
        f"{top_sellers_text}"
    )


def _auction_register_stabilization_diagnostics_handlers_v1(bot):

    @bot.message_handler(commands=["auction_sanity"])
    def auction_sanity_command_v1(message):
        from db import get_auction_diagnostics_report
        report = get_auction_diagnostics_report()
        bot.send_message(message.chat.id, build_auction_diagnostics_text_v1(report))

    @bot.message_handler(commands=["auction_fix"])
    def auction_fix_command_v1(message):
        from db import run_auction_sanity_fix
        result = run_auction_sanity_fix()
        cleanup = result.get("cleanup", {})
        after = result.get("after", {})

        text = (
            "🛠 Auction sanity fix виконано.\n\n"
            f"ACTIVE → EXPIRED_UNCLAIMED: {cleanup.get('expired_active', 0)}\n"
            f"EXPIRED_UNCLAIMED → DELETED: {cleanup.get('deleted_expired_unclaimed', 0)}\n"
            f"SOLD_UNCLAIMED → DELETED: {cleanup.get('deleted_sold_unclaimed', 0)}\n"
            f"Виправлено delete_after: {cleanup.get('fixed_missing_delete_after', 0)}\n\n"
            f"{build_auction_diagnostics_text_v1(after)}"
        )

        bot.send_message(message.chat.id, text)


try:
    _auction_base_register_handlers_before_stabilization_diagnostics_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_stabilization_diagnostics_v1 = None


def register_auction_house_handlers(bot):
    _auction_register_stabilization_diagnostics_handlers_v1(bot)

    if _auction_base_register_handlers_before_stabilization_diagnostics_v1:
        _auction_base_register_handlers_before_stabilization_diagnostics_v1(bot)
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
            "❌ Помилка під час patch_8_0_13_auction_stabilization_diagnostics.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.13 Auction stabilization/diagnostics застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- get_auction_diagnostics_report()")
    print("- run_auction_sanity_fix()")
    print("- /auction_sanity")
    print("- /auction_fix")
    print("- звіт по статусах, bad prices, missing snapshots, missing dates")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
