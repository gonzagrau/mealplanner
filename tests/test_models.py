"""Tests for domain/models.py — DataLoader and Pydantic models."""
from __future__ import annotations

import pytest
from domain.models import (
    Constraints,
    DataLoader,
    FoodGroup,
    FoodItem,
    MealType,
    Recipe,
)


@pytest.fixture(scope="module")
def loader():
    return DataLoader()


def test_load_foods(loader):
    foods = loader.load_foods()
    assert len(foods) > 0
    for food_id, food in foods.items():
        assert food.id == food_id
        assert isinstance(food, FoodItem)
        assert food.nombre
        assert food.grupo


def test_load_foods_contains_expected(loader):
    foods = loader.load_foods()
    expected_ids = ["pechuga_pollo", "huevo", "tomate", "arroz_integral", "lentejas"]
    for fid in expected_ids:
        assert fid in foods, f"Expected food '{fid}' not found in data"


def test_load_groups(loader):
    groups = loader.load_groups()
    assert len(groups) > 0
    for gid, group in groups.items():
        assert group.id == gid
        assert isinstance(group, FoodGroup)
        assert isinstance(group.items, list)


def test_load_groups_contains_expected(loader):
    groups = loader.load_groups()
    assert "proteinas_animales" in groups
    assert "verduras" in groups
    assert "frutas" in groups
    assert "almidones" in groups


def test_load_meal_types(loader):
    meal_types = loader.load_meal_types()
    assert len(meal_types) > 0
    for mt in meal_types:
        assert isinstance(mt, MealType)
        assert mt.id
        assert mt.nombre
        assert isinstance(mt.requires, list)


def test_load_constraints(loader):
    constraints = loader.load_constraints()
    assert isinstance(constraints, Constraints)
    assert constraints.max_huevos_por_dia > 0
    assert constraints.min_verduras_por_dia > 0


def test_load_recipes(loader):
    recipes = loader.load_recipes()
    assert len(recipes) > 0
    for rid, recipe in recipes.items():
        assert recipe.id == rid
        assert isinstance(recipe, Recipe)
        assert recipe.nombre
        assert recipe.tiempo_prep > 0
        assert len(recipe.ingredientes) > 0


def test_food_item_fields():
    food = FoodItem(
        id="test",
        nombre="Test Food",
        grupo="verdura",
        subgrupo="verdura_fresca",
        porcion_default=1.0,
        unidad="taza",
        notas=["nota1"],
    )
    assert food.id == "test"
    assert food.notas == ["nota1"]


def test_constraints_defaults():
    c = Constraints()
    assert c.max_huevos_por_dia == 2
    assert c.max_frutas_por_dia == 3
    assert c.max_lacteos_por_dia == 2
    assert c.min_verduras_por_dia == 2
