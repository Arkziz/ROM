# ROM Stage 21.1.X1a - виправлення identity/reference classification

- **Статус:** `GO`
- **Duplicate identities before:** `137`
- **Duplicate canonical definitions after:** `6`
- **Conflicting names before:** `127`
- **Conflicting canonical names after:** `2`
- **Unresolved references before:** `6`
- **Unresolved typed references after:** `627`

## Root cause

Stage 21.1.X1 трактував більшість полів `*_id` і `*_key` як definitions незалежно від контексту. Через це повторні quest/NPC/location/item references виглядали як дубльовані canonical identities. Name conflict також порівнював різні descriptive fields одного object path.

## Corrected semantics

- `definition_identity`: декларація canonical entity.
- `usage_reference`: посилання на already-defined entity.
- `operational_label`: джерело, provider або channel label.
- `presentation_name`: human-readable display value.
- `policy_flag`: boolean behavior setting.
- `descriptive_text`: name/title/description content.

Production code та DB/WAL/SHM не змінювалися.
