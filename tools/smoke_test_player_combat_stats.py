from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

USER_ID = 243129101


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    before = db.conn.execute(
        "SELECT hp, max_hp FROM users WHERE user_id=?", (USER_ID,)
    ).fetchone()
    require(before is not None, "test user not found")

    stats = db.get_player_stats(USER_ID)
    attack = db.get_attack(USER_ID)
    magic_attack = db.get_magic_attack(USER_ID)
    max_hp = db.get_max_hp(USER_ID)
    pdef = db.get_physical_defense(USER_ID)
    mdef = db.get_magic_defense(USER_ID)
    physical_crit = db.get_physical_crit_chance_display(USER_ID)
    magical_crit = db.get_magical_crit_chance_display(USER_ID)
    dodge = db.get_base_dodge_chance_display(USER_ID)

    after_read = db.conn.execute(
        "SELECT hp, max_hp FROM users WHERE user_id=?", (USER_ID,)
    ).fetchone()

    require(isinstance(stats, tuple) and len(stats) == 6, stats)
    require(all(isinstance(v, int) for v in stats), stats)
    require(attack == stats[0], (attack, stats))
    require(magic_attack == stats[2], (magic_attack, stats))
    require(isinstance(max_hp, int) and max_hp >= 1, max_hp)
    require(isinstance(pdef, int) and pdef >= 0, pdef)
    require(isinstance(mdef, int) and mdef >= 0, mdef)
    require(1.0 <= physical_crit <= 35.0, physical_crit)
    require(1.0 <= magical_crit <= 35.0, magical_crit)
    require(dodge == 5.0, dodge)
    require(tuple(before) == tuple(after_read), "combat-stat reads changed stored HP")

    sync = db.sync_user_max_hp(USER_ID, heal_to_full=False)
    current = db.conn.execute(
        "SELECT hp, max_hp FROM users WHERE user_id=?", (USER_ID,)
    ).fetchone()
    require(isinstance(sync, dict), type(sync))
    require(int(current[1]) == max_hp, (current, max_hp))
    require(int(current[0]) <= max_hp, (current, max_hp))

    print("[OK] player combat stats runtime contracts")
    print("- stats:", stats)
    print("- attack / magic:", attack, "/", magic_attack)
    print("- max HP:", max_hp)
    print("- PDEF / MDEF:", pdef, "/", mdef)
    print("- physical / magical crit:", round(physical_crit, 2), "/", round(magical_crit, 2))
    print("- dodge:", dodge)
    print("- HP after sync:", current[0], "/", current[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
