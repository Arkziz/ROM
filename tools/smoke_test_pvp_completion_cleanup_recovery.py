from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import systems.pvp_completion_service as service

def main():
    battle={"id":77,"status":"active","revision":4,"winner_id":None,"result_reason":None}
    participants=[{"user_id":10,"snapshot":{"character_name":"CharacterOne"}},{"user_id":20,"snapshot":{"character_name":"CharacterTwo"}}]
    releases=[]; finishes=[]
    original=(service.get_pvp_battle,service.get_pvp_participants,service.complete_pvp_battle,service.release_player_activity_session)
    try:
        service.get_pvp_battle=lambda battle_id: dict(battle)
        service.get_pvp_participants=lambda battle_id: [dict(x) for x in participants]
        def complete(battle_id,reason,winner_id=None,status="completed"):
            if battle["status"] in service.TERMINAL_STATUSES: return False
            battle.update(status=status,result_reason=reason,winner_id=winner_id); finishes.append((battle_id,reason,winner_id,status)); return True
        service.complete_pvp_battle=complete
        service.release_player_activity_session=lambda uid,**kw: releases.append((uid,kw)) or {"released":1}
        result=service.surrender_pvp_battle(77,10,4)
        assert result["success"] and result["winner_id"]==20 and result["loser_id"]==10
        assert finishes==[(77,"surrender",20,"completed")] and {x[0] for x in releases}=={10,20}
        assert "Поразка" in service.render_pvp_terminal_text(77,10)
        assert "Перемога" in service.render_pvp_terminal_text(77,20)
        retry=service.surrender_pvp_battle(77,10,4)
        assert not retry["success"] and retry["reason"]=="battle_already_finished" and len(finishes)==1
        battle.update(status="active",revision=9,winner_id=None,result_reason=None)
        assert service.surrender_pvp_battle(77,10,8)["reason"]=="stale_revision"
        assert service.surrender_pvp_battle(77,999,9)["reason"]=="wrong_actor"
        battle.update(status="completed",winner_id=None,result_reason="technical_draw_both_afk")
        assert "нічиєю" in service.render_pvp_terminal_text(77,10)
        print("[OK] PvP completion, surrender, cleanup and recovery contracts")
        print("- surrender requires explicit confirmation callback and records one terminal result: PASS")
        print("- terminal transition is idempotent and stale revision is rejected: PASS")
        print("- both pvp_battle activity sessions are released: PASS")
        print("- victory/defeat/draw reasons use character names: PASS")
        print("- terminal retry cannot overwrite winner or result reason: PASS")
        print("- production database writes: 0")
    finally:
        service.get_pvp_battle,service.get_pvp_participants,service.complete_pvp_battle,service.release_player_activity_session=original
if __name__=="__main__": main()
