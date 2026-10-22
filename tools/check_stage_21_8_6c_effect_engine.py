from rom_v2.domain.effect_engine import Effect,EffectKind,ReapplyPolicy,apply_effect,tick_start
state=apply_effect({},Effect("dot",EffectKind.DOT,1,3),ReapplyPolicy.REPLACE).effects
out=tick_start(state)
assert not out.effects and [event.amount for event in out.events]==[3,0]
print("[PASS] Stage 21.8.6c pure effect engine smoke check")
