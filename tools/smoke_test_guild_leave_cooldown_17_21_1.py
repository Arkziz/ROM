#!/usr/bin/env python3
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parent.parent
for rel in ('systems/guild_system.py','db_modules/systems_wrappers.py','db_modules/__init__.py','handlers/guild.py'):
 ast.parse((R/rel).read_text(encoding='utf-8'),filename=rel)
sys.path.insert(0,str(R));import db
db.init_guild_system()
for n in ('get_guild_join_cooldown','format_guild_join_cooldown_remaining','can_user_join_or_create_guild','leave_guild'):assert callable(getattr(db,n,None)),n
cols={r[1] for r in db.conn.execute('PRAGMA table_info(guild_membership_history)')}
assert {'user_id','guild_id','event_type','actor_user_id','occurred_at','join_blocked_until'}<=cols
assert db.can_user_join_or_create_guild(-172110001)['success'] is True
assert db.leave_guild(-172110001)['success'] is False
print('[PASS] Stage 17.21.1 canonical guild leave cooldown smoke')
