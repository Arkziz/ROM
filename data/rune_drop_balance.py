"""Canonical rune-drop balance for ROM 10.11.x."""
RUNE_DROP_CHANCES = {
    "normal": 0.05,
    "elite": 0.12,
    "boss": 0.35,
}
RUNE_LEVEL_WEIGHTS = {
    "normal": ((1, 1.00),),
    "elite": ((1, 0.80), (2, 0.20)),
    "boss": ((1, 0.60), (2, 0.35), (3, 0.05)),
}
RUNE_STAT_WEIGHTS = (
    ("STR", 0.20),
    ("STA", 0.20),
    ("DEX", 0.20),
    ("INT", 0.20),
    ("WIS", 0.20),
)
RUNE_DROP_MAX_PER_KILL = 1
RUNE_DROP_DIRECT_MAX_LEVEL = 3
RUNE_DROP_BALANCE_VERSION = "10.11.0"
