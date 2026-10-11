# Stage 20.4.3a — Simulator Potion Affordability Instrumentation

Simulator HP IDs are 401/403 and MP IDs are 402/404. Free or dropped potion use is tracked separately from purchases. When an HP/MP threshold requires a potion and no owned potion is available, the simulator may purchase and immediately use the canonical small potion if sufficient simulated gold exists: HP 5.00, MP 4.00. The final simulation event exposes HP spend, MP spend, total potion spend, repair coexistence and spend ratios. Production gameplay and database code are unchanged.
