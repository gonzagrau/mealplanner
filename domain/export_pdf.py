"""Export a WeekPlan + ShoppingList to PDF using fpdf2."""
from __future__ import annotations

from io import BytesIO

from fpdf import FPDF

from domain.models import FoodItem, MealType, ShoppingList, WeekPlan


# Group label mapping for PDF (no emojis — built-in fonts are latin-1 only)
GROUP_LABELS_PDF = {
    "proteina_animal": "Proteinas Animales",
    "proteina_vegetal": "Proteinas Vegetales",
    "huevo": "Huevos",
    "verdura": "Verduras",
    "fruta": "Frutas",
    "almidon": "Almidones",
    "lacteo": "Lacteos",
    "grasa_saludable": "Grasas Saludables",
    "condimento": "Condimentos",
}


class MealPlanPDF(FPDF):
    """Custom FPDF subclass with header/footer for the meal plan."""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Plan de Comidas Semanal", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")


def build_pdf(
    week_plan: WeekPlan,
    shopping_list: ShoppingList,
    foods: dict[str, FoodItem],
    meal_types: list[MealType],
) -> bytes:
    """Build a PDF document and return it as bytes."""
    pdf = MealPlanPDF(orientation="L", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    _render_plan_table(pdf, week_plan, foods, meal_types)

    # Shopping list on a new page (portrait)
    pdf.add_page(orientation="P")
    _render_shopping_list(pdf, shopping_list)

    # Return bytes
    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def _render_plan_table(
    pdf: MealPlanPDF,
    week_plan: WeekPlan,
    foods: dict[str, FoodItem],
    meal_types: list[MealType],
) -> None:
    """Render the weekly plan as a table."""
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Plan Semanal", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    num_cols = 1 + len(meal_types)  # Día + meal types
    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    day_col_w = 28
    meal_col_w = (page_w - day_col_w) / len(meal_types)

    # Header row
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(70, 130, 180)
    pdf.set_text_color(255, 255, 255)

    pdf.cell(day_col_w, 8, "Día", border=1, fill=True, align="C")
    for mt in meal_types:
        pdf.cell(meal_col_w, 8, mt.nombre, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 8)

    for i, day_plan in enumerate(week_plan.dias):
        meal_by_type = {meal.tipo: meal for meal in day_plan.comidas}

        # Build cell texts and compute row height
        cell_texts: list[str] = []
        for mt in meal_types:
            meal = meal_by_type.get(mt.id)
            if meal:
                parts = []
                for mi in meal.items:
                    food = foods.get(mi.id)
                    name = food.nombre if food else mi.id
                    unit = food.unidad if food else ""
                    parts.append(f"- {name} ({mi.cantidad} {unit})")
                cell_texts.append("\n".join(parts))
            else:
                cell_texts.append("-")

        # Calculate the required row height
        line_h = 4
        max_lines = 1
        for text in cell_texts:
            n_lines = max(1, len(text.split("\n")))
            if n_lines > max_lines:
                max_lines = n_lines
        row_h = max(8, max_lines * line_h + 4)

        # Check if we need a new page
        if pdf.get_y() + row_h > pdf.h - 20:
            pdf.add_page()
            # Re-draw header
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(70, 130, 180)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(day_col_w, 8, "Día", border=1, fill=True, align="C")
            for mt in meal_types:
                pdf.cell(meal_col_w, 8, mt.nombre, border=1, fill=True, align="C")
            pdf.ln()
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 8)

        # Alternating row color
        if i % 2 == 0:
            pdf.set_fill_color(240, 248, 255)
        else:
            pdf.set_fill_color(255, 255, 255)

        x_start = pdf.get_x()
        y_start = pdf.get_y()

        # Day name cell
        pdf.set_font("Helvetica", "B", 9)
        pdf.rect(x_start, y_start, day_col_w, row_h, style="DF")
        pdf.set_xy(x_start + 1, y_start + 2)
        pdf.multi_cell(day_col_w - 2, line_h, day_plan.dia, align="C")

        # Meal cells
        pdf.set_font("Helvetica", "", 8)
        x = x_start + day_col_w
        for text in cell_texts:
            pdf.rect(x, y_start, meal_col_w, row_h)
            pdf.set_xy(x + 1, y_start + 1)
            pdf.multi_cell(meal_col_w - 2, line_h, text)
            x += meal_col_w

        pdf.set_xy(x_start, y_start + row_h)


def _render_shopping_list(pdf: MealPlanPDF, shopping_list: ShoppingList) -> None:
    """Render the shopping list grouped by food category."""
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Lista de Compras", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    if not shopping_list.items:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, "Lista de compras vacía.")
        return

    grouped = shopping_list.by_group()

    for group_id, items in sorted(grouped.items()):
        label = GROUP_LABELS_PDF.get(group_id, group_id.replace("_", " ").title())

        # Check page break
        if pdf.get_y() + 12 + len(items) * 6 > pdf.h - 20:
            pdf.add_page(orientation="P")

        # Group header
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(70, 130, 180)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, f"  {label}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

        # Items
        pdf.set_font("Helvetica", "", 10)
        for item in items:
            pdf.cell(
                0, 6,
                f"    {item.nombre}: {item.cantidad} {item.unidad}",
                new_x="LMARGIN", new_y="NEXT",
            )
        pdf.ln(2)

