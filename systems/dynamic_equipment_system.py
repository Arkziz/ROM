#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thin compatibility delegates for dynamic equipment calculations.

Canonical implementation and item creation are owned by
`db_modules.generated_equipment`. This module preserves the historical public
and internal calculation signatures required by shop and maintained tools. It
contains no SQL, balance tables, random generator, or item-creation logic.
"""
from __future__ import annotations

from importlib import import_module


def _canonical():
    """Load the canonical module lazily to avoid package initialization cycles."""
    return import_module("db_modules.generated_equipment")


def get_dynamic_stat_value(item_level, rarity, base=1.0):
    return _canonical().get_dynamic_stat_value(item_level, rarity, base)


def get_dynamic_sell_price(item_level, rarity):
    return _canonical().get_dynamic_sell_price(item_level, rarity)


def get_dynamic_armor_name(slot_key, rarity):
    return _canonical().get_dynamic_armor_name(slot_key, rarity)


def init_dynamic_equipment_system():
    return _canonical().init_dynamic_equipment_system()


def add_stat_value(stats, stat_key, value):
    return _canonical().add_stat_value(stats, stat_key, value)


def get_random_main_hand_profile():
    return _canonical().get_random_main_hand_profile()


def get_random_off_hand_profile():
    return _canonical().get_random_off_hand_profile()


def get_profile_for_generated_item(slot_key, item_profile=None):
    return _canonical().get_profile_for_generated_item(slot_key, item_profile)


def get_dynamic_weapon_name(slot_key, rarity, weapon_hands=1, item_profile=None):
    return _canonical().get_dynamic_weapon_name(
        slot_key,
        rarity,
        weapon_hands,
        item_profile,
    )


def generate_dynamic_equipment_stats(
    slot_key,
    item_level,
    rarity,
    weapon_hands=1,
    item_profile=None,
):
    return _canonical().generate_dynamic_equipment_stats(
        slot_key,
        item_level,
        rarity,
        weapon_hands,
        item_profile,
    )


def normalize_equipment_restriction_value(value):
    return _canonical().normalize_equipment_restriction_value(value)


def pick_weighted_stat(weighted_stats, exclude_stat=None):
    return _canonical().pick_weighted_stat(weighted_stats, exclude_stat)


def add_primary_stat_to_stats(stats, stat_key, value):
    return _canonical().add_primary_stat_to_stats(stats, stat_key, value)


def get_existing_primary_stat_budget(stats):
    return _canonical().get_existing_primary_stat_budget(stats)


def clear_primary_stat_bonuses(stats):
    return _canonical().clear_primary_stat_bonuses(stats)


def apply_armor_type_primary_stat_profile_to_stats(stats, armor_type):
    return _canonical().apply_armor_type_primary_stat_profile_to_stats(
        stats,
        armor_type,
    )


def apply_armor_type_defense_profile_to_stats(stats, armor_type):
    return _canonical().apply_armor_type_defense_profile_to_stats(
        stats,
        armor_type,
    )


__all__ = [
    "init_dynamic_equipment_system",
    "get_dynamic_weapon_name",
    "get_dynamic_armor_name",
    "generate_dynamic_equipment_stats",
    "apply_armor_type_defense_profile_to_stats",
    "get_dynamic_sell_price",
]
