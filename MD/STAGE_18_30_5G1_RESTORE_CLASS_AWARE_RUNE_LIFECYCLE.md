# Stage 18.30.5g

Simulation-only restoration of canonical class-aware rune lifecycle.

Rune priority follows the approved class-identity policy: Warrior STR first; Knight STA first; Scout and Rogue DEX first; Mage INT first; Priest WIS first. Within the same class priority, higher rune level wins, followed by stable canonical item ID.

Runes are inserted only into equipped items with durability above zero. Canonical rune definitions and slot limits remain the owners of rune metadata and capacity. Existing sockets, quantity conservation, counters, and the existing `fuse_available_runes()` lifecycle are preserved.
