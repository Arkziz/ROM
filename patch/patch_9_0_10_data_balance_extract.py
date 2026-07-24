from pathlib import Path
from datetime import datetime
import ast
import py_compile


PATCH_NAME = "9_0_10_data_balance_extract"

BALANCE_CONSTANT_NAMES = [
    "BASE_EXP", "EXP_BASE", "EXP_MULTIPLIER", "EXP_PER_LEVEL",
    "CONTRACT_MOBS_EQUIVALENT", "CONTRACTS_UNLOCK_LEVEL", "DAILY_CONTRACT_LIMIT", "CONTRACT_TARGET_KILLS",
    "ENERGY_MAX", "ENERGY_REGEN_MINUTES", "HP_REGEN_PERCENT", "HP_REGEN_MINUTES",
    "MP_REGEN_PERCENT", "MP_REGEN_MINUTES",
    "DURABILITY_MAX", "DEATH_DURABILITY_LOSS", "REPAIR_COST_PER_DURABILITY",
    "RARITY_STAT_MULTIPLIERS", "RARITY_SELL_MULTIPLIERS", "RARITY_REPAIR_MULTIPLIERS",
    "RARITY_ORDER", "RARITY_COLORS", "RARITY_LABELS",
    "NORMAL_REFINE_STONE_DROP_CHANCE", "ELITE_REFINE_STONE_DROP_CHANCE",
    "GUILD_ELITE_MOB_EXP_REWARD", "GUILD_ELITE_MOB_RESOURCE_REWARD",
    "GUILD_CONTRACT_EXP_REWARD", "GUILD_CONTRACT_RESOURCE_REWARD",
    "AUCTION_ACTIVE_LOT_DAYS", "AUCTION_UNCLAIMED_RETENTION_DAYS", "AUCTION_MAX_ACTIVE_LOTS",
    "AUCTION_MIN_PRICE", "AUCTION_MAX_PRICE",
]

BALANCE_PREFIXES = (
    "EXP_", "CONTRACT_", "CONTRACTS_", "DAILY_CONTRACT_",
    "ENERGY_", "HP_REGEN_", "MP_REGEN_",
    "RARITY_", "REPAIR_", "DURABILITY_", "DEATH_DURABILITY_",
    "NORMAL_REFINE_", "ELITE_REFINE_",
    "GUILD_ELITE_", "GUILD_CONTRACT_",
    "AUCTION_",
)

DEFAULTS = {
    "CONTRACTS_UNLOCK_LEVEL": 5,
    "DAILY_CONTRACT_LIMIT": 5,
    "CONTRACT_TARGET_KILLS": 5,
    "CONTRACT_MOBS_EQUIVALENT": 20,
    "ENERGY_MAX": 40,
    "ENERGY_REGEN_MINUTES": 5,
    "HP_REGEN_PERCENT": 0.10,
    "HP_REGEN_MINUTES": 1,
    "NORMAL_REFINE_STONE_DROP_CHANCE": 0.08,
    "ELITE_REFINE_STONE_DROP_CHANCE": 0.20,
    "AUCTION_ACTIVE_LOT_DAYS": 7,
    "AUCTION_UNCLAIMED_RETENTION_DAYS": 30,
    "AUCTION_MAX_ACTIVE_LOTS": 20,
    "AUCTION_MIN_PRICE": "1.0",
    "AUCTION_MAX_PRICE": "999999.0",
}


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def literal_assignments_from_db(db_path):
    text = db_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    values = {}

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue

            name = target.id
            if name.startswith("_"):
                continue

            is_balance_name = name in BALANCE_CONSTANT_NAMES or name.startswith(BALANCE_PREFIXES)
            if not is_balance_name:
                continue

            try:
                value = ast.literal_eval(node.value)
            except Exception:
                continue

            if isinstance(value, (dict, list, tuple, set)) and len(value) > 100:
                continue

            values[name] = value

    for name, value in DEFAULTS.items():
        values.setdefault(name, value)

    return dict(sorted(values.items()))


def write_balance_file(root, values):
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)

    init_file = data_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("\"\"\"Static data package for ROM.\"\"\"\n", encoding="utf-8")

    target = data_dir / "balance.py"
    if target.exists():
        make_backup(root, target)

    lines = []
    lines.append('\"\"\"')
    lines.append("ROM Balance Data")
    lines.append("")
    lines.append("Static gameplay balance constants extracted from db.py during refactor 9.0.10.")
    lines.append("")
    lines.append("Important:")
    lines.append("- This file is a data module, not a gameplay system.")
    lines.append("- db.py remains the public compatibility facade for now.")
    lines.append("- Constants here must preserve the current behavior.")
    lines.append('\"\"\"')
    lines.append("")
    lines.append("# ==============================")
    lines.append("# Core constants")
    lines.append("# ==============================")
    lines.append("")

    for name, value in values.items():
        lines.append(f"{name} = {repr(value)}")

    lines.append("")
    lines.append("# ==============================")
    lines.append("# Helpers")
    lines.append("# ==============================")
    lines.append("")
    lines.append("def get_balance_value(name, default=None):")
    lines.append("    return globals().get(name, default)")
    lines.append("")
    lines.append("def as_dict():")
    lines.append("    return {")
    lines.append("        key: value")
    lines.append("        for key, value in globals().items()")
    lines.append("        if key.isupper() and not key.startswith('_')")
    lines.append("    }")
    lines.append("")

    target.write_text("\n".join(lines), encoding="utf-8")
    py_compile.compile(str(target), doraise=True)
    return target


def patch_db_import(root):
    target = root / "db.py"
    text = target.read_text(encoding="utf-8")
    marker = "# ✅ DATA BALANCE COMPATIBILITY IMPORT V1"

    if marker in text:
        return None

    backup = make_backup(root, target)
    block = 