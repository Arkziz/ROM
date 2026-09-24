"""Canonical production story-quest content registry.

Content is intentionally empty until reviewed packs of ten are installed. Runtime
integrations import this owner rather than schema fixtures, preventing fixture
quests from becoming visible or mutable in production.
"""
from types import MappingProxyType

STORY_QUEST_REGISTRY = MappingProxyType({})
