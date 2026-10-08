# Stage 19.34.4: аудит навігації, балансу та українського відмінювання

- Audit decision: **NO_GO**
- Production mutation: **NO**
- Coverage: **1–100**

## Navigation
- Required routes missing: **2**.
- Same-NPC omissions accepted: **21**.

## KILL_REGION
- Changes required: **7**.
- Quests 2/6/9 are fixed exceptions: **3/5/6**.
- Other packages use position policy **8/10[/10]**.

## Ukrainian numeral declension
- Static findings: **0**.
- Dynamic templates requiring resolver review: **7**.

## Next mutation scope
1. Add only truly missing cross-NPC routes.
2. Apply approved target changes except quests 2/6/9.
3. Correct static forms and introduce a canonical Ukrainian numeral resolver for dynamic quantities.
4. Reconcile ACTIVE target snapshots without auto-completion or duplicate rewards.
