# Stage 20.4.6a — Guild Creation Cost at Start

The first guild-creation prompt now displays the canonical creation cost and initial member limit before the player enters a name, tag or icon.

The prompt obtains values through `get_guild_creation_terms(user_id)`, matching the final confirmation screen. Guild price, atomic debit, minimum level, member limit, validation, database schema and existing guilds are unchanged.

Manual verification: open the Guild Hall, press Create Guild, and confirm the first prompt shows `50.00` gold and `10` members. Continue to the final confirmation and verify the same values remain visible.
