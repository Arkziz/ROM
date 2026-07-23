"""Energy system facade extracted from db.py in refactor 9.0.4.

This module is intentionally conservative: it delegates to the legacy db.py implementations.
Handlers can keep importing from db.py while db.py forwards calls here.
Later phases may move the real implementation here after behavior is fully verified.
"""

from importlib import import_module


def _db():
    return import_module('db')


def _call_legacy(function_name, *args, **kwargs):
    db = _db()
    legacy_name = f'_legacy_{function_name}_before_energy_system_v1'
    legacy = getattr(db, legacy_name, None)
    if legacy is None:
        raise AttributeError(f'Legacy energy function not found: {legacy_name}')
    return legacy(*args, **kwargs)


def init_energy_system(*args, **kwargs):
    return _call_legacy('init_energy_system', *args, **kwargs)


def get_user_energy(*args, **kwargs):
    return _call_legacy('get_user_energy', *args, **kwargs)
