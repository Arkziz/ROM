from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


def _event_counts(payload: Mapping[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    events = payload.get("events", [])
    if not isinstance(events, list):
        return result
    for event in events:
        if not isinstance(event, Mapping):
            continue
        key = str(event.get("event_type", ""))
        result[key] = result.get(key, 0) + 1
    return result


def _guild_values(payload: Mapping[str, Any]) -> tuple[float, float, int, int]:
    guild = payload.get("guild") or payload.get("guild_progress") or {}
    if not isinstance(guild, Mapping):
        guild = {}
    events = _event_counts(payload)
    kills = int(guild.get("kills", payload.get("wins", 0)) or 0)
    contracts = int(guild.get("contracts", events.get("contract_claim", 0)) or 0)
    exp = float(guild.get("exp", contracts * 50) or 0)
    resource = float(guild.get("resource", 0) or 0)
    return exp, resource, kills, contracts


@dataclass(frozen=True)
class GuildPopulationResult:
    players: int
    source_runs: int
    mode: str
    guild_exp: float
    guild_resource: float
    kills: int
    contracts: int
    mean_exp_per_player: float
    mean_contracts_per_player: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def simulate_guild_population(payloads: Iterable[Mapping[str, Any]], players: int) -> GuildPopulationResult:
    rows = list(payloads)
    if players <= 0:
        raise ValueError("players must be positive")
    if not rows:
        raise ValueError("at least one progression payload is required")
    values = [_guild_values(item) for item in rows]
    mean_exp = sum(item[0] for item in values) / len(values)
    mean_resource = sum(item[1] for item in values) / len(values)
    mean_kills = sum(item[2] for item in values) / len(values)
    mean_contracts = sum(item[3] for item in values) / len(values)
    # Cohort aggregation is exact for additive guild metrics once cohort means are fixed.
    mode = "EXACT" if players <= len(rows) else "FAST_COHORT"
    return GuildPopulationResult(
        players=players,
        source_runs=len(rows),
        mode=mode,
        guild_exp=round(mean_exp * players, 6),
        guild_resource=round(mean_resource * players, 6),
        kills=int(round(mean_kills * players)),
        contracts=int(round(mean_contracts * players)),
        mean_exp_per_player=round(mean_exp, 6),
        mean_contracts_per_player=round(mean_contracts, 6),
    )
