def hp_bar(current_hp, max_hp, size=10):
    if max_hp <= 0:
        return "░" * size + " 0%"

    current_hp = max(0, min(current_hp, max_hp))

    percent = int((current_hp / max_hp) * 100)
    filled = round((current_hp / max_hp) * size)

    bar = "█" * filled + "░" * (size - filled)

    return f"{bar} {percent}%"