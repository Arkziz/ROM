# Stage 19.27.17: story-boss combat keyboard parity

Guaranteed story-boss invocation now follows the normal Hunt startup sequence: create the canonical PvE encounter, replace the persistent location keyboard with `combat_placeholder_kb()`, then show `build_combat_inline_kb`. Combat mechanics and encounter ownership remain unchanged. Manual verification is required.
