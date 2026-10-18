"""Single application entrypoint for all full-stat snapshot consumers."""
from __future__ import annotations
from enum import Enum

from rom_v2.domain.full_stat_snapshot import FullStatSnapshot, FullStatSnapshotInput, build_full_stat_snapshot


class SnapshotConsumer(str, Enum):
    PROFILE = "profile"
    COMBAT = "combat"
    SIMULATOR = "simulator"


class FullStatSnapshotService:
    """Route profile, combat, and simulator through the same domain owner."""

    def build(self, source: FullStatSnapshotInput, *, consumer: SnapshotConsumer) -> FullStatSnapshot:
        if not isinstance(consumer, SnapshotConsumer):
            raise ValueError("snapshot_consumer_invalid")
        return build_full_stat_snapshot(source)

    def for_profile(self, source: FullStatSnapshotInput) -> FullStatSnapshot:
        return self.build(source, consumer=SnapshotConsumer.PROFILE)

    def for_combat(self, source: FullStatSnapshotInput) -> FullStatSnapshot:
        return self.build(source, consumer=SnapshotConsumer.COMBAT)

    def for_simulator(self, source: FullStatSnapshotInput) -> FullStatSnapshot:
        return self.build(source, consumer=SnapshotConsumer.SIMULATOR)
