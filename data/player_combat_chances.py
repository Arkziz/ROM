"""Canonical combat chance policy for ROM."""

CRIT_BASE_CHANCE = 5.0
CRIT_STAT_BASELINE = 10.0
CRIT_PER_STAT = 0.35
CRIT_MIN_CHANCE = 1.0
CRIT_MAX_CHANCE = 60.0
CRIT_SOFT_CAP_TRANSITION_STAT = 50.0
CRIT_SOFT_CAP_TRANSITION_CHANCE = 19.0
CRIT_SOFT_CAP_ASYMPTOTE = 60.0
CRIT_SOFT_CAP_RANGE = CRIT_SOFT_CAP_ASYMPTOTE - CRIT_SOFT_CAP_TRANSITION_CHANCE
CRIT_SOFT_CAP_K = CRIT_SOFT_CAP_RANGE / CRIT_PER_STAT

DODGE_BASE_CHANCE = 5.0
DODGE_PER_DEX_DELTA = 0.20
DODGE_MIN_CHANCE = 1.0
DODGE_MAX_CHANCE = 50.0
DODGE_SOFT_CAP_TRANSITION_DELTA = 40.0
DODGE_SOFT_CAP_TRANSITION_CHANCE = 13.0
DODGE_SOFT_CAP_ASYMPTOTE = 50.0
DODGE_SOFT_CAP_RANGE = DODGE_SOFT_CAP_ASYMPTOTE - DODGE_SOFT_CAP_TRANSITION_CHANCE
DODGE_SOFT_CAP_K = DODGE_SOFT_CAP_RANGE / DODGE_PER_DEX_DELTA

CRITICAL_DAMAGE_MULTIPLIER = 1.5


def clamp_chance(value, minimum, maximum):
    return max(float(minimum), min(float(maximum), float(value)))


def _calculate_crit_chance_with_soft_cap(total_stat):
    stat = float(total_stat or 0)
    if stat <= CRIT_SOFT_CAP_TRANSITION_STAT:
        return CRIT_BASE_CHANCE + max(0.0, stat - CRIT_STAT_BASELINE) * CRIT_PER_STAT
    excess = stat - CRIT_SOFT_CAP_TRANSITION_STAT
    return CRIT_SOFT_CAP_TRANSITION_CHANCE + CRIT_SOFT_CAP_RANGE * excess / (excess + CRIT_SOFT_CAP_K)


def calculate_physical_crit_chance(total_dex):
    return _calculate_crit_chance_with_soft_cap(total_dex)


def calculate_magical_crit_chance(total_wis):
    return _calculate_crit_chance_with_soft_cap(total_wis)


def calculate_dodge_chance(defender_dex, attacker_dex):
    dex_delta = float(defender_dex or 0) - float(attacker_dex or 0)
    if dex_delta <= -20.0:
        return DODGE_MIN_CHANCE
    if dex_delta <= DODGE_SOFT_CAP_TRANSITION_DELTA:
        return DODGE_BASE_CHANCE + dex_delta * DODGE_PER_DEX_DELTA
    excess = dex_delta - DODGE_SOFT_CAP_TRANSITION_DELTA
    return DODGE_SOFT_CAP_TRANSITION_CHANCE + DODGE_SOFT_CAP_RANGE * excess / (excess + DODGE_SOFT_CAP_K)


def calculate_enemy_crit_chance(player_sta):
    return clamp_chance(10.0 - (int(player_sta or 0) // 25), 0.0, 10.0)


def roll_chance(chance, rng):
    return rng.random() * 100.0 < clamp_chance(chance, 0.0, 100.0)
