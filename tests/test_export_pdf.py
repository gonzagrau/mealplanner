"""Tests for domain/export_pdf.py — PDF export."""
from __future__ import annotations

import pytest
from domain.models import DataLoader, DayPlan, Meal, MealItem, WeekPlan
from domain.shopping import ShoppingListBuilder
from domain.export_pdf import build_pdf


@pytest.fixture(scope="module")
def loader():
    return DataLoader()


@pytest.fixture(scope="module")
def foods(loader):
    return loader.load_foods()


@pytest.fixture(scope="module")
def meal_types(loader):
    return loader.load_meal_types()


def _simple_week_plan() -> WeekPlan:
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


def test_build_pdf_returns_bytes(foods, meal_types):
    plan = _simple_week_plan()
    builder = ShoppingListBuilder(foods)
    shopping_list = builder.build(plan)
    result = build_pdf(plan, shopping_list, foods, meal_types)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_build_pdf_starts_with_pdf_header(foods, meal_types):
    plan = _simple_week_plan()
    builder = ShoppingListBuilder(foods)
    shopping_list = builder.build(plan)
    result = build_pdf(plan, shopping_list, foods, meal_types)
    assert result[:5] == b"%PDF-"


def test_build_pdf_empty_plan(foods, meal_types):
    plan = WeekPlan(dias=[])
    builder = ShoppingListBuilder(foods)
    shopping_list = builder.build(plan)
    result = build_pdf(plan, shopping_list, foods, meal_types)
    assert isinstance(result, bytes)
    assert result[:5] == b"%PDF-"


def test_build_pdf_full_week(foods, meal_types, loader):
    from domain.generator import MealGenerator
    constraints = loader.load_constraints()
    groups = loader.load_groups()

    gen = MealGenerator(
        foods=foods,
        groups=groups,
        meal_types=meal_types,
        constraints=constraints,
        seed=42,
    )
    plan = gen.generate_week(days=7)
    builder = ShoppingListBuilder(foods)
    shopping_list = builder.build(plan)
    result = build_pdf(plan, shopping_list, foods, meal_types)
    assert isinstance(result, bytes)
    assert len(result) > 100
    assert result[:5] == b"%PDF-"

