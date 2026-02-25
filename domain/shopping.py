from __future__ import annotations

from collections import defaultdict

from domain.models import FoodItem, ShoppingItem, ShoppingList, WeekPlan


class ShoppingListBuilder:
    """Aggregates all ingredients from a WeekPlan into a grouped shopping list."""

    def __init__(self, foods: dict[str, FoodItem]):
        self.foods = foods

    def build(self, week_plan: WeekPlan) -> ShoppingList:
        # Aggregate totals: food_id -> total quantity
        totals: dict[str, float] = defaultdict(float)
        for day in week_plan.dias:
            for meal in day.comidas:
                for item in meal.items:
                    totals[item.id] += item.cantidad

        shopping_items: list[ShoppingItem] = []
        for food_id, cantidad in sorted(totals.items()):
            food = self.foods.get(food_id)
            if food is None:
                continue
            shopping_items.append(
                ShoppingItem(
                    nombre=food.nombre,
                    cantidad=round(cantidad, 2),
                    unidad=food.unidad,
                    grupo=food.grupo,
                )
            )

        return ShoppingList(items=shopping_items)

    def format_list(self, shopping_list: ShoppingList) -> str:
        """Format the shopping list as a human-readable string."""
        if not shopping_list.items:
            return "Lista de compras vacía."

        lines: list[str] = []
        grouped = shopping_list.by_group()

        group_labels = {
            "proteina_animal": "🥩 Proteínas Animales",
            "proteina_vegetal": "🫘 Proteínas Vegetales",
            "huevo": "🥚 Huevos",
            "verdura": "🥦 Verduras",
            "fruta": "🍎 Frutas",
            "almidon": "🌾 Almidones",
            "lacteo": "🥛 Lácteos",
            "grasa_saludable": "🫒 Grasas Saludables",
            "condimento": "🧂 Condimentos",
        }

        for group_id, items in sorted(grouped.items()):
            label = group_labels.get(group_id, group_id.replace("_", " ").title())
            lines.append(f"\n{label}")
            lines.append("-" * len(label))
            for item in items:
                lines.append(f"  • {item.nombre}: {item.cantidad} {item.unidad}")

        return "\n".join(lines).strip()
