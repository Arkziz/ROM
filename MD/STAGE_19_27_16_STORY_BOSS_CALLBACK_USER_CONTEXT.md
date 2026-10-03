# Stage 19.27.16: story-boss callback user context

Inline callback delegation now passes the player from `call.from_user` to the existing canonical `call_active_story_boss` handler while preserving the source chat. The handler still owns all eligibility, HP, encounter and boss-construction checks. No second combat pipeline is created. Manual verification is required.
