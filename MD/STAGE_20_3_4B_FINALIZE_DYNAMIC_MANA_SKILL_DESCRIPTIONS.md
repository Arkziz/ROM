# Stage 20.3.4b — Finalize Dynamic Mana Skill Descriptions

## Виправлені описи
Presentation helper тепер підтримує всі три canonical legacy-prefix формати:

```text
Витрачає N MP та ...
Витрачає N MP. ...
Витрачає N MP, ...
```

Тому `Грозове заклинання` й `Очищення віри` більше не дублюють стару fixed-ціну перед dynamic cost і формулою.

## Cooldown wording
У профілі використовується українське відмінювання:

```text
1 хід
2–4 ходи
5–20 ходів
21 хід
22–24 ходи
```

Значення cooldown не змінені.

## Незмінені системи
PvE spending, skill effects, PvP, simulator, regeneration, post-combat floor, potions і база даних не змінені.

## Ручна перевірка
Після patch достатньо відкрити профіль навичок Мага й Жреця. Повторювати бої не потрібно.
