from __future__ import annotations

import random

from domain.models import (
    Constraints,
    DayPlan,
    FoodGroup,
    FoodItem,
    Meal,
    MealItem,
    MealType,
    WeekPlan,
)
from domain.rules import RuleEngine

DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

MAX_RETRIES = 10


class MealGenerator:
    """Generates random but rule-compliant meal plans."""

    def __init__(
        self,
        foods: dict[str, FoodItem],
        groups: dict[str, FoodGroup],
        meal_types: list[MealType],
        constraints: Constraints,
        seed: int = 42,
        excluded_ids: set[str] | None = None,
        vegetarian: bool = False,
    ):
        self.foods = foods
        self.groups = groups
        self.meal_types = meal_types
        self.constraints = constraints
        self.rng = random.Random(seed)
        self.excluded_ids: set[str] = excluded_ids or set()
        self.vegetarian = vegetarian
        self.rule_engine = RuleEngine(constraints, foods, groups)

        # Pre-compute available food IDs per group (respecting exclusions/diet)
        self._group_foods: dict[str, list[str]] = {}
        for group_id, group in groups.items():
            available = [
                fid
                for fid in group.items
                if fid not in self.excluded_ids and self._diet_ok(fid)
            ]
            self._group_foods[group_id] = available

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_week(self, days: int = 7) -> WeekPlan:
        day_plans: list[DayPlan] = []
        for i in range(days):
            dia = DAYS_ES[i % len(DAYS_ES)]
            day_plans.append(self.generate_day(dia))
        return WeekPlan(dias=day_plans)

    def generate_day(self, dia: str) -> DayPlan:
        daily_tracker = self.rule_engine.new_daily_tracker()
        comidas: list[Meal] = []
        for meal_type in self.meal_types:
            meal = self._generate_meal_with_retry(meal_type, daily_tracker)
            self.rule_engine.update_tracker(meal, daily_tracker)
            comidas.append(meal)
        return DayPlan(dia=dia, comidas=comidas)

    def generate_meal(self, meal_type: MealType, daily_tracker: dict) -> Meal:
        """Generate a single meal for a given meal type."""
        items: list[MealItem] = []

        # Add one item from each required group
        for group_id in meal_type.requires:
            food_id = self._pick_from_group(group_id)
            if food_id:
                food = self.foods[food_id]
                items.append(MealItem(id=food_id, cantidad=food.porcion_default))

        # Optionally add an item from one optional group (50% chance)
        for group_id in meal_type.optional:
            if self.rng.random() < 0.5:
                food_id = self._pick_from_group(group_id)
                if food_id:
                    food = self.foods[food_id]
                    items.append(MealItem(id=food_id, cantidad=food.porcion_default))

        return Meal(tipo=meal_type.id, items=items)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_meal_with_retry(
        self, meal_type: MealType, daily_tracker: dict
    ) -> Meal:
        for _ in range(MAX_RETRIES):
            meal = self.generate_meal(meal_type, daily_tracker)
            valid, _ = self.rule_engine.validate_meal(meal, daily_tracker)
            if valid:
                return meal
        # Return last attempt even if invalid (best-effort)
        return self.generate_meal(meal_type, daily_tracker)

    def _pick_from_group(self, group_id: str) -> str | None:
        options = self._group_foods.get(group_id, [])
        if not options:
            return None
        return self.rng.choice(options)

    def _diet_ok(self, food_id: str) -> bool:
        if not self.vegetarian:
            return True
        food = self.foods.get(food_id)
        if food is None:
            return True
        return food.grupo not in ("proteina_animal",)
