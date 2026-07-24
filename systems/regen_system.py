"""
ROM Regen System
================

Refactor 9.0.5 compatibility module.

This module is intentionally conservative:
- db.py remains the public compatibility facade for handlers.
- legacy implementations are kept in db.py as _legacy_regen_v1_* references.
- this module delegates to those legacy implementations.

Important HP rules:
- dynamic max HP from equipment/refine must be respected;
- equipping/refining armor must not heal the player automatically;
- passive regeneration may heal up to dynamic max HP;
- if max HP decreases, current HP must be clamped to the new max.
"""


def _db():
    import db
    return db


def _call_legacy(name, *args, **kwargs):
    db = _db()
    legacy_name = f"_legacy_regen_v1_{name}"
    legacy = getattr(db, legacy_name, None)

    if legacy is None:
        raise AttributeError(f"Legacy regen function not found: {legacy_name}")

    return legacy(*args, **kwargs)


def _sync_hp_if_possible(user_id):
    if user_id is None:
        return None

    db = _db()
    sync = getattr(db, "sync_user_max_hp", None)

    if not sync:
        return None

    try:
        return sync(user_id, heal_to_full=False)
    except TypeError:
        return sync(user_id)
    except Exception:
        return None


def init_hp_regen_system(*args, **kwargs):
    return _call_legacy("init_hp_regen_system", *args, **kwargs)


def init_passive_regen_system(*args, **kwargs):
    return _call_legacy("init_passive_regen_system", *args, **kwargs)


def reset_hp_regen_timers_now(user_id, *args, **kwargs):
    result = _call_legacy("reset_hp_regen_timers_now", user_id, *args, **kwargs)
    _sync_hp_if_possible(user_id)
    return result


def process_passive_regeneration(user_id, *args, **kwargs):
    """
    Passive regeneration wrapper.

    Before and after legacy regeneration, sync max HP against dynamic equipment/refine bonuses.
    This protects cases where armor refine changes max HP while users.max_hp is stale.
    """

    _sync_hp_if_possible(user_id)
    result = _call_legacy("process_passive_regeneration", user_id, *args, **kwargs)
    _sync_hp_if_possible(user_id)
    return result


def apply_passive_hp_regen(user_id, *args, **kwargs):
    _sync_hp_if_possible(user_id)
    result = _call_legacy("apply_passive_hp_regen", user_id, *args, **kwargs)
    _sync_hp_if_possible(user_id)
    return result


def apply_passive_mp_regen(*args, **kwargs):
    return _call_legacy("apply_passive_mp_regen", *args, **kwargs)


def process_hp_regeneration(user_id, *args, **kwargs):
    _sync_hp_if_possible(user_id)
    result = _call_legacy("process_hp_regeneration", user_id, *args, **kwargs)
    _sync_hp_if_possible(user_id)
    return result


def process_mp_regeneration(*args, **kwargs):
    return _call_legacy("process_mp_regeneration", *args, **kwargs)


def get_hp_regen_status(*args, **kwargs):
    return _call_legacy("get_hp_regen_status", *args, **kwargs)


def get_mp_regen_status(*args, **kwargs):
    return _call_legacy("get_mp_regen_status", *args, **kwargs)
