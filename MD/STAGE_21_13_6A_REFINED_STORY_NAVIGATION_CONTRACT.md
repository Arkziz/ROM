# Stage 21.13.6a - Refined Story navigation contract

- Status: **PASS**
- Conclusion: **GO_TO_PARITY_RESOLUTION**
- Contracts: **8/8 REFINED**
- Implementation authorized: **NO**
- Database opened: **NO**
- Production mutation: **NO**
- Manual game check: **NOT_REQUIRED_CONTRACT_ONLY**

## Refined contracts
### STORY_TO_SECTION_TO_QUEST_HIERARCHY

The user flow is Story list -> Section list -> Quest list -> Quest detail; section boundaries and ordering come only from canonical hierarchy metadata.

Owners: `data/story_quest_hierarchy.py`, `handlers/story_quest_hierarchy_ui.py`

### LOCALIZED_LOCATION_AND_SECTION_NAMES

Every user-facing location and section label is resolved from canonical metadata; technical IDs are internal only.

Owners: `data/story_quest_hierarchy.py`, `systems/story_quest_location_presentation.py`

### ACTIVE_QUEST_TARGET_PRESENTATION

The active quest detail presents its current canonical objective/progress text and does not invent a target from quest type or ID.

Owners: `db_modules/story_quests.py`, `handlers/story_quest_hierarchy_ui.py`

### QUEST_STATUS_AND_PROGRESS_PRESENTATION

Quest entries distinguish active, available, locked, and completed states; progress belongs to the active quest state and completion is persistent.

Owners: `db_modules/story_quests.py`, `handlers/story_quest_hierarchy_ui.py`

### NAVIGATION_CALLBACK_AND_RETURN_PATHS

Callbacks form a bounded hierarchy and every detail/list surface returns to its immediate parent, while the root returns to the canonical profile/account surface.

Owners: `handlers/story_quest_hierarchy_ui.py`, `handlers/profile.py`

### LOCKED_AVAILABLE_COMPLETED_VISIBILITY

Visibility and labels follow V1 hierarchy policy: completed remains visible, active is identifiable, available can be opened, and locked remains non-actionable without leaking spoiler titles.

Owners: `handlers/story_quest_hierarchy_ui.py`, `data/story_quest_title_presentation.py`, `db_modules/story_quests.py`

### NO_FORBIDDEN_CHAPTER_TERM_IN_UI

All Ukrainian user-facing Story navigation uses 'розділ'; forms of 'глава' are forbidden in UI text and metadata.

Owners: `data/story_quest_hierarchy.py`, `handlers/story_quest_hierarchy_ui.py`, `handlers/profile.py`

### STABLE_ID_TO_HUMAN_LABEL_RESOLUTION

Stable story/location/section/quest IDs remain internal keys and all human labels are obtained through canonical resolvers or authoritative metadata.

Owners: `data/story_quest_hierarchy.py`, `systems/story_quest_location_presentation.py`, `data/story_quest_title_presentation.py`

## Current runtime-owner terminology evidence

Forbidden-term evidence hits requiring parity classification: **1**

## Next patch

`patch_21_13_6b_resolve_story_navigation_parity.py`
