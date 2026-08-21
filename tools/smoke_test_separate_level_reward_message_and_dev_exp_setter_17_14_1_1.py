#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
DB=ROOT/"game.db"
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
before=sha(DB)
for rel in ("handlers/combat.py","systems/contract_system.py","handlers/contracts.py","handlers/dev.py","db_modules/dev_compat.py"):
 source=(ROOT/rel).read_text(encoding="utf-8"); ast.parse(source)
 assert source.count("ROM 17.14.1.1 SEPARATE LEVEL REWARD MESSAGE AND DEV EXP SETTER")==1,rel
combat=(ROOT/"handlers/combat.py").read_text(encoding="utf-8")
assert 'reward_message = str(reward.get("exp_result", {}).get("level_up_reward_message") or "")' in combat
assert 'bot.send_message(chat_id, reward_message)' in combat
builder=next(n for n in ast.parse(combat).body if isinstance(n,ast.FunctionDef) and n.name=="build_victory_text")
builder_source=ast.get_source_segment(combat,builder) or ""
assert "level_up_reward_message" not in builder_source
assert '🏆 Новий рівень:' not in builder_source
contract=(ROOT/"systems/contract_system.py").read_text(encoding="utf-8")
assert '"level_up_reward_message":' in contract
claim=next(n for n in ast.parse(contract).body if isinstance(n,ast.FunctionDef) and n.name=="_claim_contract_reward_base")
claim_source=ast.get_source_segment(contract,claim) or ""
assert '🏆 Новий рівень:' not in claim_source
handlers=(ROOT/"handlers/contracts.py").read_text(encoding="utf-8")
assert 'reward_message = str(result.get("level_up_reward_message") or "")' in handlers
assert 'bot.send_message(call.message.chat.id, reward_message)' in handlers
dev=(ROOT/"handlers/dev.py").read_text(encoding="utf-8")
assert 'commands=["setexp"]' in dev
assert 'if not DEV_MODE:' in dev[dev.rfind("ROM 17.14.1.1"):]
compat=(ROOT/"db_modules/dev_compat.py").read_text(encoding="utf-8")
assert "def set_current_exp_for_test_17_14_1_1" in compat
setter=next(n for n in ast.parse(compat).body if isinstance(n,ast.FunctionDef) and n.name=="set_current_exp_for_test_17_14_1_1")
setter_source=ast.get_source_segment(compat,setter) or ""
assert "UPDATE users SET exp=?" in setter_source
assert "add_exp(" not in setter_source
assert "level_up_rewards" not in setter_source
assert sha(DB)==before
print("[PASS] Stage 17.14.1.1 separate reward message and DEV EXP setter contract")
