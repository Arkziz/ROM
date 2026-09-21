# Stage 18.30.11

Restores intended Warrior and Scout skill use in the simulator without changing the production skill catalog. Warrior now selects `warrior_subjugation_strike` whenever the rage threshold and cooldown allow it; `warrior_suppression` remains the debuff opener when the finisher is unavailable. Scout still opens with `scout_trap`, then applies `scout_sting_arrow` when poison is absent and the target has more than 35% HP; otherwise `scout_aimed_shot` remains the direct-damage choice. Other class selectors and canonical skill definitions are unchanged.
