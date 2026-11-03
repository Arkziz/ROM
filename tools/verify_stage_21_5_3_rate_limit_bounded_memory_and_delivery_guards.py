import ast
from pathlib import Path
p=Path("systems/telegram_rate_limit.py"); s=p.read_text(encoding="utf-8-sig"); t=ast.parse(s)
for token in ("_STATE_TTL_SECONDS","_STATE_MAX_ENTRIES","_cleanup_rate_limit_state_locked","notification_only_no_domain_replay"):
 assert token in s,token
fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=="_cleanup_rate_limit_state_locked")
assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="pop" for n in ast.walk(fn))
assert "with _LOCK" in s
print("PASS: Stage 21.5.3 bounded state and delivery policy invariants")
