from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

from systems.pvp_system import get_pvp_battle, get_pvp_participants, get_pvp_round_actions, list_active_pvp_battles, resolve_persisted_pvp_round, submit_pvp_action

log=logging.getLogger(__name__)
_started=False
_lock=threading.Lock()


def _parse(value):
    if not value: return None
    try: return datetime.fromisoformat(str(value).replace("Z","+00:00"))
    except Exception: return None


def _expired(battle):
    deadline=_parse(battle.get("action_deadline"))
    if deadline is None: return False
    if deadline.tzinfo is None: deadline=deadline.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)>=deadline


def close_expired_round(battle_id: int) -> dict[str, Any]:
    battle=get_pvp_battle(int(battle_id))
    if not battle or battle.get("status")!="active" or not _expired(battle): return {"resolved":False,"reason":"not_expired"}
    rnd=int(battle["round_number"]); rev=int(battle["revision"])
    participants=get_pvp_participants(int(battle_id)); actions=get_pvp_round_actions(int(battle_id),rnd,rev)
    acted={int(x["user_id"]) for x in actions}
    for p in participants:
        uid=int(p["user_id"])
        if uid in acted: continue
        action="stunned_skip" if bool(p.get("stunned_next")) else "afk_skip"
        try: submit_pvp_action(int(battle_id),uid,rnd,rev,action)
        except ValueError: pass
    return resolve_persisted_pvp_round(int(battle_id),rnd,rev,seed=(int(battle_id)*100000+rnd))


def start_pvp_timer_worker(on_battle_changed=None, poll_seconds: float=1.0):
    global _started
    with _lock:
        if _started: return False
        _started=True
    def worker():
        while True:
            try:
                for battle in list_active_pvp_battles():
                    if _expired(battle):
                        result=close_expired_round(int(battle["id"]))
                        if result.get("resolved") and on_battle_changed:
                            try:
                                on_battle_changed(int(battle["id"]), result)
                            except TypeError:
                                on_battle_changed(int(battle["id"]))
            except Exception:
                log.exception("PvP timer worker iteration failed")
            time.sleep(max(0.25,float(poll_seconds)))
    threading.Thread(target=worker,name="pvp-round-timer",daemon=True).start()
    return True
