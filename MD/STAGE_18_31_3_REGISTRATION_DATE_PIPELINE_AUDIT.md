# Stage 18.31.3: Аудит дати реєстрації

**Статус:** PASS  
**Режим:** READ-ONLY

## Висновок

Схема users не має canonical поля дати реєстрації; create_user не може його записувати, а UI закономірно показує fallback.

## Root cause

`NO_CANONICAL_REGISTRATION_TIMESTAMP_FIELD`

## Наступний підетап

Stage 18.31.4 має виправити canonical запис, збереження, читання та legacy policy без зміни інших account timestamps.
