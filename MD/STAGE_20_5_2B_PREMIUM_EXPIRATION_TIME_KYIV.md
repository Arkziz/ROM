# Stage 20.5.2b — Premium Expiration Time in Kyiv

Premium expiration remains stored and compared as canonical UTC. User-facing Premium screens and account status now convert the timestamp to `Europe/Kyiv` and display `DD.MM.YYYY HH:MM за Києвом`.

Registration date, other timestamps, entitlement duration, expiration logic, Premium formulas, tariffs, loot, simulator and database are unchanged.

Manual verification: compare the account Premium status and Premium detail page. Both must show the same local date and time with the suffix `за Києвом`.
