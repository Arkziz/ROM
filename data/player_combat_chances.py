"""Canonical player combat chance policy for ROM Stage 18.13."""
CRIT_BASE_CHANCE=5.0
CRIT_STAT_BASELINE=10.0
CRIT_PER_STAT=0.35
CRIT_MIN_CHANCE=1.0
CRIT_MAX_CHANCE=35.0
DODGE_BASE_CHANCE=5.0
DODGE_PER_DEX_DELTA=0.20
DODGE_MIN_CHANCE=1.0
DODGE_MAX_CHANCE=30.0
CRITICAL_DAMAGE_MULTIPLIER=1.5
def clamp_chance(value,minimum,maximum): return max(float(minimum),min(float(maximum),float(value)))
def calculate_physical_crit_chance(total_dex): return clamp_chance(CRIT_BASE_CHANCE+max(0.0,float(total_dex)-CRIT_STAT_BASELINE)*CRIT_PER_STAT,CRIT_MIN_CHANCE,CRIT_MAX_CHANCE)
def calculate_magical_crit_chance(total_wis): return clamp_chance(CRIT_BASE_CHANCE+max(0.0,float(total_wis)-CRIT_STAT_BASELINE)*CRIT_PER_STAT,CRIT_MIN_CHANCE,CRIT_MAX_CHANCE)
def calculate_dodge_chance(defender_dex,attacker_dex): return clamp_chance(DODGE_BASE_CHANCE+(float(defender_dex)-float(attacker_dex))*DODGE_PER_DEX_DELTA,DODGE_MIN_CHANCE,DODGE_MAX_CHANCE)
def calculate_enemy_crit_chance(player_sta): return clamp_chance(10.0-(int(player_sta or 0)//25),0.0,10.0)
def roll_chance(chance,rng): return rng.random()*100.0 < clamp_chance(chance,0.0,100.0)
