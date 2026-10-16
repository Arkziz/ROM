# ROM Stage 21.1.X1 - canonical content inventory

- **Статус:** `GO`
- **Проаналізовано content sources:** `65`
- **Python content sources:** `65`
- **Non-Python content sources:** `0`
- **Extracted identity/name/reference records:** `1205`
- **Content groups:** `12`

## Content groups

### `classes`

- Sources: **12**
- Records: **23**
- Identifiers/keys: **0**
- Names/text: **23**
- References: **0**

### `events`

- Sources: **1**
- Records: **0**
- Identifiers/keys: **0**
- Names/text: **0**
- References: **0**

### `items`

- Sources: **23**
- Records: **31**
- Identifiers/keys: **4**
- Names/text: **27**
- References: **0**

### `localization`

- Sources: **21**
- Records: **49**
- Identifiers/keys: **4**
- Names/text: **45**
- References: **0**

### `locations`

- Sources: **7**
- Records: **74**
- Identifiers/keys: **34**
- Names/text: **38**
- References: **2**

### `mobs`

- Sources: **8**
- Records: **66**
- Identifiers/keys: **29**
- Names/text: **34**
- References: **3**

### `npcs`

- Sources: **2**
- Records: **0**
- Identifiers/keys: **0**
- Names/text: **0**
- References: **0**

### `progression`

- Sources: **18**
- Records: **23**
- Identifiers/keys: **0**
- Names/text: **23**
- References: **0**

### `quests`

- Sources: **28**
- Records: **1073**
- Identifiers/keys: **849**
- Names/text: **223**
- References: **1**

### `shops_economy`

- Sources: **9**
- Records: **8**
- Identifiers/keys: **4**
- Names/text: **4**
- References: **0**

### `skills`

- Sources: **5**
- Records: **0**
- Identifiers/keys: **0**
- Names/text: **0**
- References: **0**

### `uncategorized_content`

- Sources: **5**
- Records: **0**
- Identifiers/keys: **0**
- Names/text: **0**
- References: **0**

## Review queues

- Duplicate identities: **137**.
- Conflicting names for one identity: **127**.
- Reference candidates without known identity: **6**.
- Historical/superseded candidates: **9**.
- Technical IDs without localized name evidence: **0**.
- Dynamic content symbols requiring manual extraction: **130**.

## Canonical V2 content contract

- Stable IDs і keys не перевикористовуються для іншої сутності.
- Кожна reference повинна resolve до canonical identity відповідного namespace.
- Користувацькі тексти використовують локалізовані людські назви, а не technical IDs.
- Content проходить schema validation до startup; invalid reference блокує bootstrap.
- Historical, candidate, shadow і superseded values не мігруються без окремого owner рішення.
- Runtime mutation logic не зберігається в content catalogs.
- Quest terminology: історія -> розділи -> квести; термін `глава` не є canonical.
- Canonical location presentation використовує `Початок Шляху`, а не `start_path`/`Start Path`.
- Production DB/WAL/SHM не відкривалися та не змінювалися.

## Наступний етап

Stage 21.1.X2 - Behavioral fixtures ROM V1.
