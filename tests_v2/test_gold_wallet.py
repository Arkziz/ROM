import unittest
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal

from rom_v2.application.gold_wallet import (
    GoldDirection, GoldWalletCommand, GoldWalletConflictError,
    GoldWalletContractError, GoldWalletOperation, GoldWalletService,
    normalize_gold,
)


class MemoryWallet:
    def __init__(self, balance=Decimal("0.00")):
        self.balances={1: balance}; self.operations={}
    def get_balance(self, account_id): return self.balances.get(account_id, Decimal("0.00"))
    def set_balance(self, account_id, balance): self.balances[account_id]=balance
    def get_operation(self, operation_key): return self.operations.get(operation_key)
    def add_operation(self, operation):
        if operation.operation_key in self.operations: raise RuntimeError("duplicate_operation")
        self.operations[operation.operation_key]=operation


class MemoryUnitOfWork:
    def __init__(self, balance=Decimal("0.00"), fail_commit=False):
        self.wallet=MemoryWallet(balance); self.fail_commit=fail_commit
        self.commits=0; self.rollbacks=0; self._snapshot=None
    def begin(self): self._snapshot=(deepcopy(self.wallet.balances),deepcopy(self.wallet.operations))
    def now(self): return datetime(2026,1,2,3,4,5,tzinfo=timezone.utc)
    def commit(self):
        if self.fail_commit: raise RuntimeError("commit_failure")
        self.commits+=1; self._snapshot=None
    def rollback(self):
        self.rollbacks+=1
        if self._snapshot is not None:
            self.wallet.balances,self.wallet.operations=self._snapshot
            self._snapshot=None


def command(key="op-1", direction=GoldDirection.CREDIT, amount=Decimal("1.00"), reason="test"):
    return GoldWalletCommand(key,1,direction,amount,reason)


class GoldWalletTests(unittest.TestCase):
    def execute(self, uow, cmd): uow.begin(); return GoldWalletService().execute(cmd,uow)
    def test_credit_quantizes_half_up(self):
        uow=MemoryUnitOfWork(Decimal("2.00")); result=self.execute(uow,command(amount=Decimal("1.005")))
        self.assertEqual(result.operation.balance_after,Decimal("3.01")); self.assertEqual(uow.commits,1)
    def test_debit_exact_balance(self):
        uow=MemoryUnitOfWork(Decimal("2.00")); result=self.execute(uow,command(direction=GoldDirection.DEBIT,amount=Decimal("2.00")))
        self.assertEqual(result.operation.balance_after,Decimal("0.00"))
    def test_insufficient_funds_fails_without_mutation(self):
        uow=MemoryUnitOfWork(Decimal("1.00"))
        with self.assertRaisesRegex(GoldWalletContractError,"insufficient_funds"): self.execute(uow,command(direction=GoldDirection.DEBIT,amount=Decimal("1.01")))
        self.assertEqual(uow.wallet.get_balance(1),Decimal("1.00")); self.assertFalse(uow.wallet.operations); self.assertEqual(uow.commits,0)
    def test_same_payload_replay_returns_original_without_commit(self):
        uow=MemoryUnitOfWork(); first=self.execute(uow,command()); uow.begin(); second=GoldWalletService().execute(command(),uow)
        self.assertTrue(second.replayed); self.assertEqual(second.operation,first.operation); self.assertEqual(uow.commits,1)
    def test_changed_payload_replay_conflicts(self):
        uow=MemoryUnitOfWork(); self.execute(uow,command())
        uow.begin()
        with self.assertRaises(GoldWalletConflictError): GoldWalletService().execute(command(amount=Decimal("2.00")),uow)
        self.assertEqual(uow.wallet.get_balance(1),Decimal("1.00"))
    def test_commit_failure_rolls_back_balance_and_history(self):
        uow=MemoryUnitOfWork(fail_commit=True)
        with self.assertRaisesRegex(RuntimeError,"commit_failure"): self.execute(uow,command())
        self.assertEqual(uow.wallet.get_balance(1),Decimal("0.00")); self.assertFalse(uow.wallet.operations); self.assertEqual(uow.rollbacks,1)
    def test_float_is_rejected(self):
        with self.assertRaisesRegex(GoldWalletContractError,"amount_must_be_decimal"): normalize_gold(1.0)
    def test_non_finite_decimal_is_rejected(self):
        with self.assertRaisesRegex(GoldWalletContractError,"amount_must_be_finite"): normalize_gold(Decimal("NaN"))
    def test_zero_and_negative_amount_rejected(self):
        for value in (Decimal("0"),Decimal("-1")):
            with self.subTest(value=value), self.assertRaisesRegex(GoldWalletContractError,"amount_must_be_positive"):
                GoldWalletService().execute(command(amount=value),MemoryUnitOfWork())
    def test_required_stable_fields(self):
        for cmd,reason in ((command(key=""),"operation_key_required"),(GoldWalletCommand("x",0,GoldDirection.CREDIT,Decimal("1"),"r"),"account_id_must_be_positive"),(command(reason=""),"reason_code_required")):
            with self.subTest(reason=reason), self.assertRaisesRegex(GoldWalletContractError,reason): GoldWalletService().execute(cmd,MemoryUnitOfWork())
    def test_immutable_operation(self):
        uow=MemoryUnitOfWork(); operation=self.execute(uow,command()).operation
        with self.assertRaises(Exception): operation.amount=Decimal("9.00")
    def test_restart_replay_uses_persisted_operation(self):
        first=MemoryUnitOfWork(); original=self.execute(first,command())
        restarted=MemoryUnitOfWork(); restarted.wallet.balances=deepcopy(first.wallet.balances); restarted.wallet.operations=deepcopy(first.wallet.operations); restarted.begin()
        replay=GoldWalletService().execute(command(),restarted)
        self.assertTrue(replay.replayed); self.assertEqual(replay.operation,original.operation); self.assertEqual(restarted.commits,0)


if __name__ == "__main__": unittest.main()
