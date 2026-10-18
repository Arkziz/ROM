# Stage 21.6.1 — Account domain

## Canonical owners

- Aggregate: `rom_v2.domain.account.Account`
- Application service: `rom_v2.application.account_service.AccountService`
- Persistence adapter: `rom_v2.infrastructure.persistence.account_repository.SQLiteAccountRepository`
- UoW adapter: `rom_v2.infrastructure.persistence.account_unit_of_work.SQLiteAccountUnitOfWork`

## Contract

Telegram identity is positive and unique. Registration time is explicit UTC ISO-8601. Account status uses stable keys `active`, `blocked`, and `closed`. Closing is terminal. Bag capacity and optimistic version are account-level state. Registration atomically creates the account and zero crystal wallet through one Unit of Work. Repeated registration by Telegram identity returns the existing account without mutation. Presentation text is outside the domain result.

## Manual verification

Not required. This stage has no Telegram or gameplay presentation flow.
