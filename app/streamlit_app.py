from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so domain imports work
# when Streamlit runs this file directly (e.g. streamlit run app/streamlit_app.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from domain.models import DataLoader
from domain.generator import MealGenerator
from domain.shopping import ShoppingListBuilder
from domain.export_pdf import build_pdf


def main():
    st.set_page_config(page_title="🥗 Planificador de Comidas", layout="wide")
    st.title("🥗 Planificador de Comidas Semanal")

    loader = DataLoader()
    foods = loader.load_foods()
    groups = loader.load_groups()
    meal_types = loader.load_meal_types()
    constraints = loader.load_constraints()

    # ----------------------------------------------------------------
    # Sidebar controls
    # ----------------------------------------------------------------
    with st.sidebar:
        st.header("⚙️ Configuración")
        days = st.slider("Número de días", min_value=1, max_value=14, value=7)
        seed = st.number_input("Semilla aleatoria", min_value=0, max_value=9999, value=42)
        vegetarian = st.toggle("Vegetariano (excluir proteínas animales)", value=False)

        all_food_ids = sorted(foods.keys())
        exclude_items = st.multiselect(
            "Alimentos a excluir",
            options=all_food_ids,
            format_func=lambda fid: foods[fid].nombre,
        )

        generate_btn = st.button("🚀 Generar Plan", type="primary", use_container_width=True)

    if not generate_btn:
        st.info("Ajusta los parámetros en el panel lateral y pulsa **Generar Plan**.")
        return

    excluded_ids = set(exclude_items)

    generator = MealGenerator(
        foods=foods,
        groups=groups,
        meal_types=meal_types,
        constraints=constraints,
        seed=int(seed),
        excluded_ids=excluded_ids,
        vegetarian=vegetarian,
    )

    week_plan = generator.generate_week(days=days)

    # ----------------------------------------------------------------
    # Weekly plan table
    # ----------------------------------------------------------------
    st.subheader("📅 Plan Semanal")

    header_cols = ["Día"] + [mt.nombre for mt in meal_types]

    rows = []
    for day_plan in week_plan.dias:
        meal_by_type = {meal.tipo: meal for meal in day_plan.comidas}
        row = {"Día": day_plan.dia}
        for mt in meal_types:
            meal = meal_by_type.get(mt.id)
            if meal:
                parts = []
                for mi in meal.items:
                    food = foods.get(mi.id)
                    name = food.nombre if food else mi.id
                    parts.append(f"{name} ({mi.cantidad} {food.unidad if food else ''})")
                row[mt.nombre] = " | ".join(parts)
            else:
                row[mt.nombre] = "-"
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ----------------------------------------------------------------
    # PDF download
    # ----------------------------------------------------------------
    builder = ShoppingListBuilder(foods=foods)
    shopping_list = builder.build(week_plan)

    pdf_bytes = build_pdf(week_plan, shopping_list, foods, meal_types)
    st.download_button(
        label="📄 Descargar Plan en PDF",
        data=pdf_bytes,
        file_name="plan_comidas.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    # ----------------------------------------------------------------
    # Shopping list
    # ----------------------------------------------------------------
    st.subheader("🛒 Lista de Compras")

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

    cols = st.columns(2)
    items_per_col = (len(grouped) + 1) // 2

    for i, (group_id, items) in enumerate(sorted(grouped.items())):
        col = cols[i // items_per_col] if items_per_col > 0 else cols[0]
        label = group_labels.get(group_id, group_id.replace("_", " ").title())
        with col:
            with st.expander(label, expanded=True):
                for item in items:
                    st.markdown(f"- **{item.nombre}**: {item.cantidad} {item.unidad}")

    # ----------------------------------------------------------------
    # Recipe details
    # ----------------------------------------------------------------
    recipes = loader.load_recipes()
    if recipes:
        st.subheader("📖 Recetas Sugeridas")
        for recipe in recipes.values():
            with st.expander(f"{recipe.nombre} ({recipe.tiempo_prep} min)"):
                st.markdown(f"**Tiempo de preparación:** {recipe.tiempo_prep} minutos")
                st.markdown("**Ingredientes:**")
                for ing in recipe.ingredientes:
                    food = foods.get(ing.item)
                    name = food.nombre if food else ing.item
                    st.markdown(f"  - {name}: {ing.cantidad} {ing.unidad}")
                st.markdown(f"[Ver receta completa]({recipe.url})")


if __name__ == "__main__":
    main()
