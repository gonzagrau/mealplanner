from __future__ import annotations

from domain.models import Constraints, FoodGroup, FoodItem, Meal


class RuleEngine:
    """Validates meals and daily plans against nutritional constraints."""

    def __init__(
        self,
        constraints: Constraints,
        foods: dict[str, FoodItem],
        groups: dict[str, FoodGroup],
    ):
        self.constraints = constraints
        self.foods = foods
        self.groups = groups
        # Build reverse map: food_id -> group_id
        self._food_to_group: dict[str, str] = {}
        for group in groups.values():
            for food_id in group.items:
                self._food_to_group[food_id] = group.id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def new_daily_tracker(self) -> dict:
        return {
            "eggs_today": 0,
            "fruits_today": 0,
            "lacteos_today": 0,
            "verduras_today": 0,
            "item_counts": {},
        }

    def validate_meal(self, meal: Meal, daily_tracker: dict) -> tuple[bool, list[str]]:
        """Validate a meal against current daily tracker state.

        Returns (is_valid, list_of_violations).
        """
        violations: list[str] = []

        # Simulate what would happen if we add this meal
        tentative_eggs = daily_tracker["eggs_today"]
        tentative_fruits = daily_tracker["fruits_today"]
        tentative_lacteos = daily_tracker["lacteos_today"]

        for meal_item in meal.items:
            food = self.foods.get(meal_item.id)
            if food is None:
                violations.append(f"Alimento desconocido: {meal_item.id}")
                continue

            if food.grupo == "huevo":
                tentative_eggs += meal_item.cantidad
            elif food.grupo == "fruta":
                tentative_fruits += meal_item.cantidad
            elif food.grupo == "lacteo":
                tentative_lacteos += meal_item.cantidad

        if tentative_eggs > self.constraints.max_huevos_por_dia:
            violations.append(
                f"Límite de huevos excedido: {tentative_eggs} > "
                f"{self.constraints.max_huevos_por_dia}"
            )
        if tentative_fruits > self.constraints.max_frutas_por_dia:
            violations.append(
                f"Límite de frutas excedido: {tentative_fruits} > "
                f"{self.constraints.max_frutas_por_dia}"
            )
        if tentative_lacteos > self.constraints.max_lacteos_por_dia:
            violations.append(
                f"Límite de lácteos excedido: {tentative_lacteos} > "
                f"{self.constraints.max_lacteos_por_dia}"
            )

        return len(violations) == 0, violations

    def check_daily_limits(self, daily_tracker: dict) -> tuple[bool, list[str]]:
        """Check whether the daily plan meets all daily limits."""
        violations: list[str] = []

        if daily_tracker["verduras_today"] < self.constraints.min_verduras_por_dia:
            violations.append(
                f"Pocas verduras: {daily_tracker['verduras_today']} < "
                f"{self.constraints.min_verduras_por_dia}"
            )

        return len(violations) == 0, violations

    def update_tracker(self, meal: Meal, daily_tracker: dict) -> None:
        """Update the daily tracker with the items from a meal."""
        for meal_item in meal.items:
            food = self.foods.get(meal_item.id)
            if food is None:
                continue

            if food.grupo == "huevo":
                daily_tracker["eggs_today"] += meal_item.cantidad
            elif food.grupo == "fruta":
                daily_tracker["fruits_today"] += meal_item.cantidad
            elif food.grupo == "lacteo":
                daily_tracker["lacteos_today"] += meal_item.cantidad
            elif food.grupo == "verdura":
                daily_tracker["verduras_today"] += meal_item.cantidad

            counts = daily_tracker["item_counts"]
            counts[meal_item.id] = counts.get(meal_item.id, 0) + meal_item.cantidad
