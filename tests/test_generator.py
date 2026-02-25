"""Tests for domain/generator.py — MealGenerator."""
from __future__ import annotations

import pytest
from domain.models import DataLoader, WeekPlan
from domain.generator import MealGenerator


@pytest.fixture(scope="module")
def base_data():
    loader = DataLoader()
    return {
        "foods": loader.load_foods(),
        "groups": loader.load_groups(),
        "meal_types": loader.load_meal_types(),
        "constraints": loader.load_constraints(),
    }


def make_generator(base_data, seed=42, vegetarian=False, excluded_ids=None):
    return MealGenerator(
        foods=base_data["foods"],
        groups=base_data["groups"],
        meal_types=base_data["meal_types"],
        constraints=base_data["constraints"],
        seed=seed,
        vegetarian=vegetarian,
        excluded_ids=excluded_ids,
    )


# ------------------------------------------------------------------
# generate_week tests
# ------------------------------------------------------------------

def test_generate_week_returns_correct_number_of_days(base_data):
    gen = make_generator(base_data)
    plan = gen.generate_week(days=7)
    assert isinstance(plan, WeekPlan)
    assert len(plan.dias) == 7


def test_generate_week_correct_day_names(base_data):
    gen = make_generator(base_data)
    plan = gen.generate_week(days=7)
    from domain.generator import DAYS_ES
    for i, day_plan in enumerate(plan.dias):
        assert day_plan.dia == DAYS_ES[i]


def test_generate_week_partial_days(base_data):
    gen = make_generator(base_data)
    plan = gen.generate_week(days=3)
    assert len(plan.dias) == 3


def test_generate_week_more_than_7_days(base_data):
    gen = make_generator(base_data)
    plan = gen.generate_week(days=10)
    assert len(plan.dias) == 10


# ------------------------------------------------------------------
# Reproducibility tests
# ------------------------------------------------------------------

def test_same_seed_produces_same_output(base_data):
    gen1 = make_generator(base_data, seed=99)
    gen2 = make_generator(base_data, seed=99)
    plan1 = gen1.generate_week(days=7)
    plan2 = gen2.generate_week(days=7)
    assert plan1.model_dump() == plan2.model_dump()


def test_different_seeds_produce_different_outputs(base_data):
    gen1 = make_generator(base_data, seed=1)
    gen2 = make_generator(base_data, seed=2)
    plan1 = gen1.generate_week(days=7)
    plan2 = gen2.generate_week(days=7)
    # Very unlikely to be identical with different seeds
    assert plan1.model_dump() != plan2.model_dump()


# ------------------------------------------------------------------
# Meal structure tests
# ------------------------------------------------------------------

def test_each_day_has_meals(base_data):
    gen = make_generator(base_data)
    plan = gen.generate_week(days=7)
    for day_plan in plan.dias:
        assert len(day_plan.comidas) > 0


def test_each_meal_has_items(base_data):
    gen = make_generator(base_data)
    plan = gen.generate_week(days=7)
    for day_plan in plan.dias:
        for meal in day_plan.comidas:
            assert len(meal.items) > 0


def test_all_food_ids_exist(base_data):
    gen = make_generator(base_data)
    plan = gen.generate_week(days=7)
    for day_plan in plan.dias:
        for meal in day_plan.comidas:
            for item in meal.items:
                assert item.id in base_data["foods"], f"Unknown food id: {item.id}"


# ------------------------------------------------------------------
# Vegetarian / exclusion tests
# ------------------------------------------------------------------

def test_vegetarian_excludes_animal_proteins(base_data):
    gen = make_generator(base_data, vegetarian=True)
    plan = gen.generate_week(days=7)
    animal_ids = {
        fid
        for fid, food in base_data["foods"].items()
        if food.grupo == "proteina_animal"
    }
    for day_plan in plan.dias:
        for meal in day_plan.comidas:
            for item in meal.items:
                assert item.id not in animal_ids, (
                    f"Animal protein '{item.id}' appeared in vegetarian plan"
                )


def test_excluded_ids_not_in_plan(base_data):
    excluded = {"salmon", "pechuga_pollo"}
    gen = make_generator(base_data, excluded_ids=excluded)
    plan = gen.generate_week(days=7)
    for day_plan in plan.dias:
        for meal in day_plan.comidas:
            for item in meal.items:
                assert item.id not in excluded
