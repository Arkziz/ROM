# ROM Stage 21.1.X1 - canonical content inventory

- **Canonical revision:** `Stage 21.1.X1a`
- **Статус:** `GO`
- **Content sources:** `65`
- **Extracted records:** `1205`
- **Definition identities:** `141`
- **Usage references:** `749`
- **Operational labels:** `3`
- **Presentation names:** `2`
- **Policy flags:** `1`

## Виправлення Stage 21.1.X1a

- Definition identities відокремлено від usage references.
- Повторне використання reference більше не рахується duplicate identity.
- Operational source labels винесено в окрему категорію.
- Human-readable boss/NPC/location values класифікуються як presentation names.
- Boolean policy values не аналізуються як references.
- Name conflict визначається лише для одного canonical identity та одного name field.

## Review queues

- Duplicate canonical definitions: **6**.
- Conflicting names for one canonical identity: **2**.
- Unresolved typed usage references: **627**.
- Ambiguous identities requiring owner review: **0**.
- Historical/superseded candidates: **9**.
- Dynamic symbols requiring extraction: **130**.

## Canonical V2 content contract

- Stable identity належить одному authoritative definition owner.
- Usage references можуть повторюватися необмежено, але повинні resolve до definition identity.
- Operational labels і presentation names не є canonical IDs.
- Invalid typed reference блокує V2 content bootstrap.
- Historical/candidate/shadow values потребують окремого owner-рішення.
- Technical IDs не показуються користувачу замість локалізованих назв.
- Production DB/WAL/SHM не відкривалися й не змінювалися.

## Наступний етап

Stage 21.1.X2 - Behavioral fixtures ROM V1.
