# Stage 18.30.9a

Fixes the committed 10-day diagnostic runner to use the canonical `exp_gained` field exposed by the progression payload. The nonexistent `final_exp` field is removed from summary and XLSX output. Gameplay and canonical progression remain unchanged.
