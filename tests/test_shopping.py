"""Tests for domain/shopping.py — ShoppingListBuilder."""
from __future__ import annotations

import pytest
from domain.models import DataLoader, DayPlan, Meal, MealItem, WeekPlan
from domain.shopping import ShoppingListBuilder


@pytest.fixture(scope="module")
def foods():
    return DataLoader().load_foods()


@pytest.fixture(scope="module")
def builder(foods):
    return ShoppingListBuilder(foods)


def _simple_week_plan() -> WeekPlan:
    """A minimal deterministic week plan for testing."""
    day = DayPlan(
        dia="Lunes",
        comidas=[
            Meal(tipo="desayuno", items=[
                MealItem(id="avena", cantidad=0.5),
                MealItem(id="manzana", cantidad=1),
            ]),
            Meal(tipo="almuerzo", items=[
                MealItem(id="pechuga_pollo", cantidad=1),
                MealItem(id="tomate", cantidad=1),
                MealItem(id="arroz_integral", cantidad=0.5),
            ]),
        ],
    )
    return WeekPlan(dias=[day])


# ------------------------------------------------------------------
# build tests
# ------------------------------------------------------------------

def test_build_returns_non_empty_list(builder):
    plan = _simple_week_plan()
    shopping_list = builder.build(plan)
    assert len(shopping_list.items) > 0


def test_build_aggregates_quantities(builder):
    # Two days with same item should sum quantities
    day1 = DayPlan(
        dia="Lunes",
        comidas=[Meal(tipo="desayuno", items=[MealItem(id="manzana", cantidad=1)])],
    )
    day2 = DayPlan(
        dia="Martes",
        comidas=[Meal(tipo="desayuno", items=[MealItem(id="manzana", cantidad=1)])],
    )
    plan = WeekPlan(dias=[day1, day2])
    shopping_list = builder.build(plan)
    manzana_items = [i for i in shopping_list.items if i.nombre == "Manzana"]
    assert len(manzana_items) == 1
    assert manzana_items[0].cantidad == 2.0


def test_build_contains_correct_food_names(builder):
    plan = _simple_week_plan()
    shopping_list = builder.build(plan)
    names = {item.nombre for item in shopping_list.items}
    assert "Avena" in names
    assert "Manzana" in names
    assert "Pechuga de pollo" in names


def test_build_sets_correct_grupo(builder):
    plan = _simple_week_plan()
    shopping_list = builder.build(plan)
    by_name = {item.nombre: item for item in shopping_list.items}
    assert by_name["Manzana"].grupo == "fruta"
    assert by_name["Pechuga de pollo"].grupo == "proteina_animal"


def test_build_empty_plan(builder):
    plan = WeekPlan(dias=[])
    shopping_list = builder.build(plan)
    assert shopping_list.items == []


# ------------------------------------------------------------------
# format_list tests
# ------------------------------------------------------------------

def test_format_list_non_empty(builder):
    plan = _simple_week_plan()
    shopping_list = builder.build(plan)
    result = builder.format_list(shopping_list)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_list_contains_food_names(builder):
    plan = _simple_week_plan()
    shopping_list = builder.build(plan)
    result = builder.format_list(shopping_list)
    assert "Manzana" in result
    assert "Pechuga de pollo" in result


def test_format_list_empty_shopping_list(builder):
    from domain.models import ShoppingList
    empty = ShoppingList(items=[])
    result = builder.format_list(empty)
    assert "vacía" in result.lower()


def test_format_list_contains_group_headers(builder):
    plan = _simple_week_plan()
    shopping_list = builder.build(plan)
    result = builder.format_list(shopping_list)
    # Should contain at least one group emoji header
    assert any(emoji in result for emoji in ["🥩", "🥦", "🍎", "🌾", "🥛", "🫒", "🫘", "🥚"])


# ------------------------------------------------------------------
# by_group tests
# ------------------------------------------------------------------

def test_by_group_organises_items(builder):
    plan = _simple_week_plan()
    shopping_list = builder.build(plan)
    grouped = shopping_list.by_group()
    assert isinstance(grouped, dict)
    assert "fruta" in grouped
    assert "proteina_animal" in grouped
