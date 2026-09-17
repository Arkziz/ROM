# Stage 18.29: Pilot Event Continuation Manifest

## Baseline

Continue from the production commit created by Stage 18.28.9.

## Required first decision

Before mutation, approve the pilot event policy: `EVENT_KEY`, display name, UTC dates, locations, encounter chance, mob template, event currency, drop quantity and chance, shop price, reward item, item policies and post-event behavior.

## Planned sub-stages

1. `18.29.1` Approve pilot content and economy policy.
2. `18.29.2` Add production event package and reserve block `4000..4049`.
3. `18.29.3` Add required item catalog persistence and atomic shop exchange.
4. `18.29.4` Add Telegram event UI and stale-callback lifecycle guards.
5. `18.29.5` Perform direct manual pilot acceptance.
6. `18.29.6` Close the pilot and update complete documentation.

## Minimum pilot vertical slice

- One normal event mob.
- One stackable character-bound event currency.
- One event drop rule.
- One atomic exchange offer.
- One persistent event reward item.
- No event boss unless separately approved.

## Mandatory acceptance

Verify inactive and active lifecycle, encounter selection, event drop, ordinary-mob isolation, insufficient currency, successful exchange, full inventory, repeated callback, restart behavior, `END_AT`, retained item resolution and ordinary gameplay regression.
