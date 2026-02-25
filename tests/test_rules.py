"""Tests for domain/rules.py — RuleEngine."""
from __future__ import annotations

import pytest
from domain.models import Constraints, DataLoader, Meal, MealItem
from domain.rules import RuleEngine


@pytest.fixture(scope="module")
def rule_engine():
    loader = DataLoader()
    foods = loader.load_foods()
    groups = loader.load_groups()
    constraints = loader.load_constraints()
    return RuleEngine(constraints, foods, groups)


@pytest.fixture(scope="module")
def foods():
    return DataLoader().load_foods()


def _tracker(eggs=0, fruits=0, lacteos=0, verduras=0):
    return {
        "eggs_today": eggs,
        "fruits_today": fruits,
        "lacteos_today": lacteos,
        "verduras_today": verduras,
        "item_counts": {},
    }


# ------------------------------------------------------------------
# validate_meal tests
# ------------------------------------------------------------------

def test_validate_meal_valid(rule_engine, foods):
    meal = Meal(tipo="almuerzo", items=[
        MealItem(id="pechuga_pollo", cantidad=1),
        MealItem(id="tomate", cantidad=1),
    ])
    valid, violations = rule_engine.validate_meal(meal, _tracker())
    assert valid
    assert violations == []


def test_validate_meal_egg_limit_exceeded(rule_engine):
    # Already used max eggs; adding 2 more should violate
    tracker = _tracker(eggs=2)
    meal = Meal(tipo="cena", items=[MealItem(id="huevo", cantidad=2)])
    valid, violations = rule_engine.validate_meal(meal, tracker)
    assert not valid
    assert any("huevo" in v.lower() for v in violations)


def test_validate_meal_fruit_limit_exceeded(rule_engine):
    tracker = _tracker(fruits=3)
    meal = Meal(tipo="merienda", items=[MealItem(id="manzana", cantidad=1)])
    valid, violations = rule_engine.validate_meal(meal, tracker)
    assert not valid
    assert any("fruta" in v.lower() for v in violations)


def test_validate_meal_lacteo_limit_exceeded(rule_engine):
    tracker = _tracker(lacteos=2)
    meal = Meal(tipo="desayuno", items=[MealItem(id="yogur_descremado", cantidad=1)])
    valid, violations = rule_engine.validate_meal(meal, tracker)
    assert not valid
    assert any("lácteo" in v.lower() for v in violations)


def test_validate_meal_unknown_food(rule_engine):
    meal = Meal(tipo="almuerzo", items=[MealItem(id="nonexistent_food_xyz", cantidad=1)])
    valid, violations = rule_engine.validate_meal(meal, _tracker())
    assert not valid
    assert any("desconocido" in v.lower() for v in violations)


# ------------------------------------------------------------------
# check_daily_limits tests
# ------------------------------------------------------------------

def test_check_daily_limits_ok(rule_engine):
    tracker = _tracker(verduras=3)
    valid, violations = rule_engine.check_daily_limits(tracker)
    assert valid
    assert violations == []


def test_check_daily_limits_too_few_verduras(rule_engine):
    tracker = _tracker(verduras=0)
    valid, violations = rule_engine.check_daily_limits(tracker)
    assert not valid
    assert any("verdura" in v.lower() for v in violations)


# ------------------------------------------------------------------
# update_tracker tests
# ------------------------------------------------------------------

def test_update_tracker_eggs(rule_engine):
    tracker = _tracker()
    meal = Meal(tipo="desayuno", items=[MealItem(id="huevo", cantidad=2)])
    rule_engine.update_tracker(meal, tracker)
    assert tracker["eggs_today"] == 2


def test_update_tracker_fruits(rule_engine):
    tracker = _tracker()
    meal = Meal(tipo="merienda", items=[MealItem(id="manzana", cantidad=1)])
    rule_engine.update_tracker(meal, tracker)
    assert tracker["fruits_today"] == 1


def test_update_tracker_verduras(rule_engine):
    tracker = _tracker()
    meal = Meal(tipo="almuerzo", items=[
        MealItem(id="tomate", cantidad=1),
        MealItem(id="lechuga", cantidad=2),
    ])
    rule_engine.update_tracker(meal, tracker)
    assert tracker["verduras_today"] == 3


def test_update_tracker_item_counts(rule_engine):
    tracker = _tracker()
    meal = Meal(tipo="almuerzo", items=[MealItem(id="pechuga_pollo", cantidad=1)])
    rule_engine.update_tracker(meal, tracker)
    assert tracker["item_counts"]["pechuga_pollo"] == 1


def test_new_daily_tracker(rule_engine):
    tracker = rule_engine.new_daily_tracker()
    assert tracker["eggs_today"] == 0
    assert tracker["fruits_today"] == 0
    assert tracker["lacteos_today"] == 0
    assert tracker["verduras_today"] == 0
    assert tracker["item_counts"] == {}
