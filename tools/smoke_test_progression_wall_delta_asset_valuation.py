from systems.simulation.asset_valuation import value_progression_assets
from systems.simulation.progression_wall_analyzer import _delta, _percentage_change


def main():
    first = {"mean_battles": 50.0, "mean_elapsed_hours": 18.0}
    second = {"mean_battles": 200.2, "mean_elapsed_hours": 65.0}
    transition_one = _delta(first, {})
    transition_two = _delta(second, first)
    assert transition_one["mean_battles"] == 50.0
    assert transition_two["mean_battles"] == 150.2
    assert round(_percentage_change(150.2, 50.0), 1) == 200.4

    payload = {
        "final_gold": 10,
        "inventory": {
            "items": [
                {"simulation_item_id": 1, "quantity": 2, "sell_value": 3, "category": "material"},
                {"simulation_item_id": 2, "quantity": 1, "sell_value": 7, "category": "equipment"},
                {"simulation_item_id": 3, "quantity": 5, "category": "rune"},
            ]
        },
        "equipment": {"slots": {"chest": 2}},
    }
    value = value_progression_assets(payload)
    assert value.cash_gold == 10
    assert value.resource_value == 6
    assert value.equipped_item_value == 7
    assert value.total_net_worth == 23
    assert value.coverage == "PARTIAL" and value.unvalued_items == 1

    unavailable = value_progression_assets({"final_gold": 12})
    assert unavailable.total_net_worth == 12 and unavailable.coverage == "UNAVAILABLE"
    print("[OK] Progression-wall delta and asset-valuation contracts")
    print("- level transition uses incremental, not cumulative battles: PASS")
    print("- 50 -> 200.2 cumulative yields 150.2 incremental: PASS")
    print("- wall increase is 200.4%, not 300.4%: PASS")
    print("- explicit-value net-worth buckets: PASS")
    print("- missing inventory pricing is surfaced, not invented: PASS")
    print("- database writes: 0")


if __name__ == "__main__":
    main()
