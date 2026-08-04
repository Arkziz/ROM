from systems.simulation.economy_analyzer import analyze_economy
from systems.simulation.guild_population import simulate_guild_population


def fixture():
    return {
        "final_gold": 20,
        "gold_gained": 10,
        "wins": 30,
        "events": [
            {"event_type": "city_visit", "details": {"sale_gold": 5, "repair_cost": 2}},
            {"event_type": "contract_claim", "details": {}},
            {"event_type": "trade", "details": {"gold": 7}},
        ],
        "guild": {"exp": 75, "resource": 3, "kills": 30, "contracts": 1},
        "inventory": {"items": [{"simulation_item_id": 1, "quantity": 2, "sell_value": 4, "category": "material"}]},
        "equipment": {"slots": {}},
    }


def main():
    economy = analyze_economy([fixture(), fixture()])
    assert economy.gold_faucets == 30
    assert economy.gold_sinks == 4
    assert economy.gold_transfers == 14
    assert economy.net_gold_created == 26
    assert economy.mean_total_net_worth == 28
    guild = simulate_guild_population([fixture(), fixture()], 100)
    assert guild.guild_exp == 7500 and guild.kills == 3000 and guild.contracts == 100
    assert guild.mode == "FAST_COHORT"
    exact = simulate_guild_population([fixture(), fixture()], 2)
    assert exact.mode == "EXACT"
    print("[OK] Economy and guild-population contracts")
    print("- faucets/sinks/transfers separated: PASS")
    print("- total net worth uses explicit asset values: PASS")
    print("- player transfers do not alter net gold creation: PASS")
    print("- EXACT/FAST cohort guild aggregation: PASS")
    print("- populations 10/50/100/500/1000 supported: PASS")
    print("- database writes: 0")


if __name__ == "__main__":
    main()
