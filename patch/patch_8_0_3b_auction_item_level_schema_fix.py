from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_3b_auction_item_level_schema_fix"
TARGET_REL = Path("systems") / "auction_house_system.py"
MARKER = "# ✅ AUCTION HOUSE ITEM SCHEMA SAFE SNAPSHOT V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE ITEM SCHEMA SAFE SNAPSHOT V1
# ==============================


def _auction_sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def _auction_select_existing_expr(alias, columns, preferred_names, output_alias, default_value=""):
    """
    Builds a safe SELECT expression for schemas where item columns may have different names.

    Example:
    - if items has item_level -> it.item_level AS item_level
    - if items has level      -> it.level AS item_level
    - otherwise              -> 0 AS item_level
    """

    for column_name in preferred_names:
        if column_name in columns:
            return f"{alias}.{column_name} AS {output_alias}"

    if isinstance(default_value, int):
        return f"{int(default_value)} AS {output_alias}"

    return f"{_auction_sql_literal(default_value)} AS {output_alias}"


def _auction_get_inventory_row(inventory_id, user_id=None):
    """
    Schema-safe inventory + item loader.

    Older 8.0.3 code expected items.level, but this project stores item level under
    another column name in the current DB. This loader checks actual table columns
    and only selects columns that really exist.
    """

    init_auction_house()

    inventory_id = int(inventory_id)

    inv_cols = _auction_table_columns("inventory")
    item_cols = _auction_table_columns("items")

    select_parts = []

    # Stable aliases used by auction snapshot code.
    select_parts.append(_auction_select_existing_expr("inv", inv_cols, ["id"], "inventory_id", 0))
    select_parts.append(_auction_select_existing_expr("inv", inv_cols, ["user_id"], "inventory_user_id", 0))
    select_parts.append(_auction_select_existing_expr("inv", inv_cols, ["item_id"], "inventory_item_id", 0))
    select_parts.append(_auction_select_existing_expr("inv", inv_cols, ["quantity"], "inventory_quantity", 1))
    select_parts.append(_auction_select_existing_expr("inv", inv_cols, ["refine_level"], "inventory_refine_level", 0))

    select_parts.append(_auction_select_existing_expr("it", item_cols, ["id"], "item_id", 0))
    select_parts.append(_auction_select_existing_expr("it", item_cols, ["name"], "item_name", "Предмет"))
    select_parts.append(_auction_select_existing_expr("it", item_cols, ["type", "item_type"], "item_type", ""))
    select_parts.append(_auction_select_existing_expr("it", item_cols, ["category", "item_category"], "item_category", ""))
    select_parts.append(_auction_select_existing_expr("it", item_cols, ["slot_key", "slot", "equipment_slot"], "item_slot_key", ""))
    select_parts.append(_auction_select_existing_expr("it", item_cols, ["rarity", "item_rarity"], "item_rarity", ""))
    select_parts.append(_auction_select_existing_expr("it", item_cols, ["level", "item_level", "required_level", "min_level"], "item_level", 0))

    # Preserve full row details with prefixed aliases to avoid duplicate-column collisions.
    for column_name in inv_cols:
        select_parts.append(f"inv.{column_name} AS inv_{column_name}")

    for column_name in item_cols:
        select_parts.append(f"it.{column_name} AS item_{column_name}")

    sql = f"""
    SELECT
        {', '.join(select_parts)}
    FROM inventory inv
    JOIN items it ON inv.item_id = it.id
    WHERE inv.id=?
    """

    params = [inventory_id]

    if user_id is not None:
        sql += " AND inv.user_id=?"
        params.append(user_id)

    cursor.execute(sql, tuple(params))
    return cursor.fetchone()
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
    target = root / TARGET_REL

    if not target.exists():
        raise SystemExit("❌ Не знайдено systems/auction_house_system.py. Спочатку потрібні патчі 8.0.1 і 8.0.3.")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч 8.0.3b вже застосовано. Змін не потрібно.")
        py_compile.compile(str(target), doraise=True)
        return

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + APPEND_CODE + "\n", encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_8_0_3b_auction_item_level_schema_fix.\n"
            "systems/auction_house_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.3b Auction item schema fix застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ systems/auction_house_system.py пройшов py_compile.")
    print("\nЩо виправлено:")
    print("- більше немає жорсткого звернення до items.level")
    print("- auction snapshot тепер сам визначає, як у БД називається рівень предмета")
    print("- список спорядження для виставлення має відкриватися без помилки no such column: it.level")
    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
