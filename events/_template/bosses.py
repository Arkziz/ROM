# -*- coding: utf-8 -*-
"""Event boss data only; combat behavior remains canonical."""
BOSS_CANDIDATES: tuple[dict, ...] = ()

def get_boss_candidates(context) -> tuple[dict, ...]:
    return BOSS_CANDIDATES
