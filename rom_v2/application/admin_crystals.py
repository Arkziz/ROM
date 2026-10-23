from dataclasses import dataclass
class AdminCrystalsContractError(ValueError):pass
class AdminCrystalsConflictError(AdminCrystalsContractError):pass
@dataclass(frozen=True,slots=True)
class AdminCrystalAdjustmentCommand:operation_key:str;actor_user_id:int;target_user_id:int;adjustment_kind:str;requested_amount:int;expected_balance_before:int;preview_applied_amount:int;reason:str=""
@dataclass(frozen=True,slots=True)
class AdminCrystalAdjustmentReceipt:operation_key:str;actor_user_id:int;target_user_id:int;adjustment_kind:str;requested_amount:int;applied_amount:int;balance_before:int;balance_after:int;reason:str
@dataclass(frozen=True,slots=True)
class AdminCrystalNotification:operation_key:str;target_user_id:int;adjustment_kind:str;applied_amount:int;balance_after:int
@dataclass(frozen=True,slots=True)
class AdminCrystalAdjustmentResult:receipt:AdminCrystalAdjustmentReceipt;notification:AdminCrystalNotification;replayed:bool
class AdminCrystalAdjustmentService:
 def execute(self,c,u):
  if not c.operation_key.strip():raise AdminCrystalsContractError("operation_key_required")
  if c.requested_amount<=0:raise AdminCrystalsContractError("positive_amount_required")
  try:
   old=u.receipts.get_receipt(c.operation_key)
   if old:
    if (old.actor_user_id,old.target_user_id,old.adjustment_kind,old.requested_amount,old.balance_before,old.applied_amount)!=(c.actor_user_id,c.target_user_id,c.adjustment_kind,c.requested_amount,c.expected_balance_before,c.preview_applied_amount):raise AdminCrystalsConflictError("operation_key_payload_conflict")
    return AdminCrystalAdjustmentResult(old,self.notice(old),True)
   if not u.authorization.is_admin(c.actor_user_id):raise AdminCrystalsContractError("admin_authorization_required")
   if not u.accounts.exists(c.target_user_id):raise AdminCrystalsContractError("target_account_not_found")
   before=u.wallet.get_balance(c.target_user_id)
   if before!=c.expected_balance_before:raise AdminCrystalsContractError("stale_balance")
   applied=c.requested_amount if c.adjustment_kind=="credit" else min(c.requested_amount,before)
   if applied!=c.preview_applied_amount:raise AdminCrystalsContractError("stale_applied_amount")
   after=u.wallet.credit(c.target_user_id,applied) if c.adjustment_kind=="credit" else (u.wallet.debit(c.target_user_id,applied) if applied else before)
   r=AdminCrystalAdjustmentReceipt(c.operation_key,c.actor_user_id,c.target_user_id,c.adjustment_kind,c.requested_amount,applied,before,after,c.reason.strip());u.ledger.append(r);u.receipts.save_receipt(r);n=self.notice(r);u.notifications.enqueue(n);u.commit();return AdminCrystalAdjustmentResult(r,n,False)
  except Exception:u.rollback();raise
 @staticmethod
 def notice(r):return AdminCrystalNotification(r.operation_key,r.target_user_id,r.adjustment_kind,r.applied_amount,r.balance_after)
