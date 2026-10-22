from datetime import datetime, timedelta, timezone
import unittest

from rom_v2.domain.battle_persistence import (
    BattlePersistenceContractFailure, PersistedEncounterStatus, PersistedEncounterTerminalOutcome,
    begin_persisted_encounter, claim_persisted_encounter_terminal, expire_persisted_encounter_once, select_expired_persisted_encounters,
    find_active_persisted_encounter, recover_persisted_encounters_after_restart,
)


class BattlePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.marker = begin_persisted_encounter("e-1", "actor-1", self.t0, self.t0 + timedelta(minutes=5))

    def test_begin_and_read_active(self):
        self.assertEqual(find_active_persisted_encounter([self.marker], "actor-1"), self.marker)
        self.assertEqual(self.marker.status, PersistedEncounterStatus.ACTIVE)

    def test_terminal_claim_is_absorbing_and_idempotent(self):
        first = claim_persisted_encounter_terminal(self.marker, PersistedEncounterTerminalOutcome.VICTORY, "op-1", self.t0 + timedelta(minutes=1))
        duplicate = claim_persisted_encounter_terminal(first.marker, PersistedEncounterTerminalOutcome.VICTORY, "op-1", self.t0 + timedelta(minutes=2))
        conflict = claim_persisted_encounter_terminal(first.marker, PersistedEncounterTerminalOutcome.DEFEAT, "op-2", self.t0 + timedelta(minutes=2))
        self.assertTrue(first.accepted)
        self.assertTrue(duplicate.duplicate)
        self.assertFalse(conflict.accepted)
        self.assertEqual(conflict.marker, first.marker)

    def test_expiry_boundary_and_restart_recovery(self):
        before = expire_persisted_encounter_once(self.marker, self.t0 + timedelta(minutes=4))
        self.assertEqual(before.reason, "not_expired")
        recovered = recover_persisted_encounters_after_restart([self.marker], self.t0 + timedelta(minutes=5))
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0].marker.status, PersistedEncounterStatus.EXPIRED)
        self.assertEqual(recover_persisted_encounters_after_restart([recovered[0].marker], self.t0 + timedelta(minutes=6)), ())

    def test_expired_selection_is_deterministic(self):
        later = begin_persisted_encounter("e-2", "actor-2", self.t0, self.t0 + timedelta(minutes=4))
        found = select_expired_persisted_encounters([self.marker, later], self.t0 + timedelta(minutes=5))
        self.assertEqual([m.encounter_id for m in found], ["e-2", "e-1"])

    def test_multiple_active_for_actor_fails_closed(self):
        other = begin_persisted_encounter("e-2", "actor-1", self.t0, self.t0 + timedelta(minutes=7))
        with self.assertRaises(BattlePersistenceContractFailure):
            find_active_persisted_encounter([self.marker, other], "actor-1")

    def test_naive_time_rejected(self):
        with self.assertRaises(BattlePersistenceContractFailure):
            begin_persisted_encounter("e", "a", datetime(2026, 1, 1), self.t0 + timedelta(minutes=1))

    def test_marker_has_no_full_battle_snapshot_fields(self):
        self.assertFalse(hasattr(self.marker, "turn"))
        self.assertFalse(hasattr(self.marker, "rng_state"))
        self.assertFalse(hasattr(self.marker, "cooldowns"))
        self.assertFalse(hasattr(self.marker, "effects"))


if __name__ == "__main__":
    unittest.main()
