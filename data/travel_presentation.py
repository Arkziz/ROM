# -*- coding: utf-8 -*-
"""Canonical, spoiler-free presentation metadata for location travel."""
from __future__ import annotations

UNKNOWN_LOCATION_NAME = "🧭 Невідома місцевість"

ROUTE_PRESENTATION = {
    ("city", "start_path"): {
        "preview": "За міськими мурами починаються відкриті землі та дороги, якими мандрівники вирушають назустріч новим випробуванням.",
        "active": "Міські ворота залишаються позаду, а дорога веде до відкритих земель.",
        "arrival": "Навколо простягаються відкриті землі та дороги, якими проходять мандрівники, торговці й найманці.",
    },
    ("start_path", "city"): {
        "preview": "Попереду знайома дорога до міських воріт, за якими чекають крамниці, майстерні та безпечний відпочинок.",
        "active": "Стежка поступово переходить у широку дорогу, що веде до міських воріт.",
        "arrival": "За міськими воротами знову відкриті крамниці, майстерні та знайомі вулиці.",
    },
    ("start_path", "dark_forest"): {
        "preview": "Попереду лежить лісова стежка. Дерева стають густішими, а світла між кронами дедалі менше.",
        "active": "Відкрита місцевість залишається позаду, а стежка веде між високими деревами вглиб лісу.",
        "arrival": "Густі крони затуляють небо, а між деревами простягаються вузькі лісові стежки.",
    },
    ("dark_forest", "start_path"): {
        "preview": "Лісова стежка веде до світліших і відкритіших земель за межами густого бору.",
        "active": "Дерева поступово рідшають, і попереду знову з’являється відкрита дорога.",
        "arrival": "Після тісних лісових стежок перед тобою знову відкриваються широкі дороги та просторі землі.",
    },
}

CITY_MAP_INTRO = "Місто — безпечний осередок торгівлі, ремесел і відпочинку. Звідси починається дорога до земель за міськими мурами."
CITY_DESTINATION_SUMMARY = "Відкриті землі та дороги неподалік від Міста."

def get_node_name(node_id, world_nodes):
    """Return a localized canonical name and never expose a raw technical ID."""
    return (world_nodes.get(str(node_id)) or {}).get("name") or UNKNOWN_LOCATION_NAME

def get_route_presentation(from_node, to_node):
    """Return approved route metadata or safe generic text for an unknown edge."""
    return ROUTE_PRESENTATION.get((str(from_node), str(to_node)), {
        "preview": "Попереду дорога до обраного пункту призначення.",
        "active": "Подорож триває за обраним маршрутом.",
        "arrival": "Подорож завершено, і перед тобою відкривається нова місцевість.",
    })

def format_arrival_destination(node_id, world_nodes):
    """Use natural Ukrainian destination grammar for known travel nodes."""
    key=str(node_id)
    if key=="city": return "Ти прибув до Міста."
    if key=="start_path": return "Ти прибув до локації «Початок Шляху»."
    if key=="dark_forest": return "Ти прибув до Темного Бору."
    return f"Ти прибув до місцевості «{get_node_name(key, world_nodes)}»."
