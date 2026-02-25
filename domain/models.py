from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, field_validator


def get_data_dir() -> Path:
    """Find the data/ directory relative to this file or the project root."""
    # Try relative to this file (domain/models.py -> parent -> data/)
    candidate = Path(__file__).parent.parent / "data"
    if candidate.exists():
        return candidate
    # Try current working directory
    candidate = Path.cwd() / "data"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Cannot locate data/ directory from {Path(__file__)}")


# ---------------------------------------------------------------------------
# Core food models
# ---------------------------------------------------------------------------

class FoodItem(BaseModel):
    id: str
    nombre: str
    grupo: str
    subgrupo: str
    porcion_default: float
    unidad: str
    notas: list[str] = []


class FoodGroup(BaseModel):
    id: str
    nombre: str
    items: list[str]


# ---------------------------------------------------------------------------
# Meal structure models
# ---------------------------------------------------------------------------

class PortionRule(BaseModel):
    grupo: str
    cantidad: float
    unidad: str


class MealType(BaseModel):
    id: str
    nombre: str
    requires: list[str]
    optional: list[str] = []
    rules: list[PortionRule] = []


class Constraints(BaseModel):
    max_huevos_por_dia: int = 2
    max_frutas_por_dia: int = 3
    max_lacteos_por_dia: int = 2
    pizza_por_semana: int = 1
    min_verduras_por_dia: int = 2


# ---------------------------------------------------------------------------
# Recipe models
# ---------------------------------------------------------------------------

class RecipeIngredient(BaseModel):
    item: str
    cantidad: float
    unidad: str


class Recipe(BaseModel):
    id: str
    nombre: str
    ingredientes: list[RecipeIngredient]
    tiempo_prep: int
    url: str


# ---------------------------------------------------------------------------
# Plan models
# ---------------------------------------------------------------------------

class MealItem(BaseModel):
    id: str
    cantidad: float


class Meal(BaseModel):
    tipo: str  # meal type id
    items: list[MealItem]


class DayPlan(BaseModel):
    dia: str
    comidas: list[Meal]


class WeekPlan(BaseModel):
    dias: list[DayPlan]


# ---------------------------------------------------------------------------
# Shopping models
# ---------------------------------------------------------------------------

class ShoppingItem(BaseModel):
    nombre: str
    cantidad: float
    unidad: str
    grupo: str


class ShoppingList(BaseModel):
    items: list[ShoppingItem]

    def by_group(self) -> dict[str, list[ShoppingItem]]:
        """Return items grouped by food group."""
        result: dict[str, list[ShoppingItem]] = {}
        for item in self.items:
            result.setdefault(item.grupo, []).append(item)
        return result


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

class DataLoader:
    """Loads all JSON data files from the data/ directory."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or get_data_dir()

    def _load(self, filename: str) -> list | dict:
        path = self.data_dir / filename
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def load_foods(self) -> dict[str, FoodItem]:
        raw = self._load("foods.json")
        return {item["id"]: FoodItem(**item) for item in raw}

    def load_groups(self) -> dict[str, FoodGroup]:
        raw = self._load("groups.json")
        return {g["id"]: FoodGroup(**g) for g in raw}

    def load_meal_types(self) -> list[MealType]:
        raw = self._load("meal_types.json")
        return [MealType(**mt) for mt in raw]

    def load_constraints(self) -> Constraints:
        raw = self._load("constraints.json")
        return Constraints(**raw)

    def load_recipes(self) -> dict[str, Recipe]:
        raw = self._load("recipes.json")
        return {r["id"]: Recipe(**r) for r in raw}
