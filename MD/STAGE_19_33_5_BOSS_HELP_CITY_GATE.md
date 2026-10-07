# Stage 19.33.5: виправлення location gate для boss-help

HELP callback квестів 49/99 тепер перевіряє active production BOSS lifecycle без вимоги перебувати в локації боса. Це дозволяє відкрити підказку у Голови Найманців у Місті. INVOKE і надалі проходить окрему canonical перевірку current location через `_presentation_for_user`; бойовий gate не послаблено. DB, progress, rewards і WAL/SHM не змінювалися. Manual verification: REQUIRED.
