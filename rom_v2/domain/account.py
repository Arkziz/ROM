"""V1-faithful account aggregate for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone

@dataclass(frozen=True,slots=True)
class Account:
    """Represent only V1-confirmed account identity and persistent entitlements."""
    account_id:str
    telegram_user_id:int
    registered_at_utc:str
    bag_capacity:int
    def __post_init__(self)->None:
        if not self.account_id.strip():raise ValueError("account_id_required")
        if self.telegram_user_id<=0:raise ValueError("telegram_user_id_must_be_positive")
        try: parsed=datetime.fromisoformat(self.registered_at_utc.replace("Z","+00:00"))
        except ValueError as error:raise ValueError("registered_at_utc_invalid") from error
        if parsed.tzinfo is None or parsed.utcoffset()!=timezone.utc.utcoffset(parsed):raise ValueError("registered_at_utc_must_be_utc")
        if self.bag_capacity<1:raise ValueError("bag_capacity_out_of_range")
