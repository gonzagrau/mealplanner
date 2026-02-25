from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path so domain imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from domain.models import DataLoader
from domain.generator import MealGenerator
from domain.shopping import ShoppingListBuilder

console = Console()


def generate(
    days: int = typer.Option(7, "--days", "-d", help="Número de días a planificar"),
    seed: int = typer.Option(42, "--seed", "-s", help="Semilla aleatoria para reproducibilidad"),
    vegetarian: bool = typer.Option(False, "--vegetarian", "-v", help="Excluir proteínas animales"),
    exclude: Optional[list[str]] = typer.Option(
        None, "--exclude", "-e", help="ID de alimento a excluir (repetible)"
    ),
    no_shopping_list: bool = typer.Option(
        False, "--no-shopping-list", help="Omitir lista de compras"
    ),
):
    """Genera un plan de comidas y (opcionalmente) la lista de compras."""
    loader = DataLoader()
    foods = loader.load_foods()
    groups = loader.load_groups()
    meal_types = loader.load_meal_types()
    constraints = loader.load_constraints()

    excluded_ids: set[str] = set(exclude) if exclude else set()

    generator = MealGenerator(
        foods=foods,
        groups=groups,
        meal_types=meal_types,
        constraints=constraints,
        seed=seed,
        excluded_ids=excluded_ids,
        vegetarian=vegetarian,
    )

    console.print(f"\n[bold cyan]🥗 Generando plan de {days} días (semilla={seed})[/bold cyan]\n")

    week_plan = generator.generate_week(days=days)

    # Build meal-type label map
    mt_labels = {mt.id: mt.nombre for mt in meal_types}

    # ----------------------------------------------------------------
    # Weekly plan table
    # ----------------------------------------------------------------
    table = Table(title="Plan Semanal", box=box.ROUNDED, show_lines=True)
    table.add_column("Día", style="bold yellow", min_width=12)
    for mt in meal_types:
        table.add_column(mt.nombre, min_width=20)

    for day_plan in week_plan.dias:
        # Index meals by type
        meal_by_type = {meal.tipo: meal for meal in day_plan.comidas}
        row = [day_plan.dia]
        for mt in meal_types:
            meal = meal_by_type.get(mt.id)
            if meal:
                food_names = []
                for mi in meal.items:
                    food = foods.get(mi.id)
                    name = food.nombre if food else mi.id
                    food_names.append(f"{name} ({mi.cantidad} {food.unidad if food else ''})")
                row.append("\n".join(food_names))
            else:
                row.append("-")
        table.add_row(*row)

    console.print(table)

    if not no_shopping_list:
        builder = ShoppingListBuilder(foods=foods)
        shopping_list = builder.build(week_plan)
        formatted = builder.format_list(shopping_list)
        console.print(f"\n[bold cyan]🛒 Lista de Compras[/bold cyan]\n")
        console.print(formatted)

    console.print("\n[bold green]✅ Plan generado correctamente.[/bold green]\n")
