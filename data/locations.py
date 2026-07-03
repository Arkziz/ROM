LOCATIONS = {
    "start_path": {
        "id": "start_path",
        "name": "🌿 Початок Шляху",
        "description": (
            "Перші стежки за межами табору мандрівників. "
            "Тут ще не панує справжня темрява, але за деревами вже чути "
            "рух диких звірів, шурхіт павутини та слабке світіння рунічних рослин. "
            "Саме тут новачки вчаться виживати, берегти спорядження, "
            "користуватися зіллями та повертатися до міста перед тим, "
            "як ризик стане занадто великим."
        ),
        "level_min": 1,
        "level_max": 5,
        "unlock_level": 1,
        "boss": "🐺 Ватажок зграї",
        "mobs": [
            "🐗 Дикий кабан",
            "🌱 Рунічний паросток",
            "🦡 Лісовий борсук",
            "💎 Рунічний слимак",
            "🦇 Лісовий кажан",
            "🩸 Печерний кровосос",
            "🕷️ Малий павук",
            "🧪 Павук-кислотник",
            "🐺 Молодий вовк",
            "👻 Вовк-примара",
        ]
    },

    "dark_forest": {
        "id": "dark_forest",
        "name": "🌲 Темний Бір",
        "description": (
            "Глибша частина лісу, куди не заходять випадкові подорожні. "
            "Між старими деревами ховаються гоблінські дозори, шамани, "
            "берсерки та слуги темних рун. Повітря тут важче, "
            "а кожен крок може привести до засідки або стародавніх руїн."
        ),
        "level_min": 6,
        "level_max": 10,
        "unlock_level": 6,
        "boss": "👑 Король Гоблінів",
        "mobs": [
            "👺 Малий гоблін",
            "🧪 Гоблін-знахар",
            "🗡️ Гоблін-розвідник",
            "🧙 Гоблін-шаман",
            "🪓 Гоблін-берсерк",
            "🔥 Гоблін-піроман",
            "🛡️ Гоблін-страж",
            "🔮 Рунічний культист",
            "🧟 Осквернений воїн",
            "🕯️ Осквернений віщун",
        ]
    }
}


LOCATION_ORDER = [
    "start_path",
    "dark_forest"
]


def get_location(location_id):
    return LOCATIONS.get(location_id, LOCATIONS["start_path"])


def get_unlocked_locations(player_level):
    result = []

    for location_id in LOCATION_ORDER:
        location = LOCATIONS[location_id]

        if player_level >= location["unlock_level"]:
            result.append(location)

    return result


def is_location_unlocked(location_id, player_level):
    location = LOCATIONS.get(location_id)

    if not location:
        return False

    return player_level >= location["unlock_level"]