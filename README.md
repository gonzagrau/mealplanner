# 🥗 Meal Planner

A **rule-based weekly meal planner** that generates constraint-compliant menus and aggregated shopping lists — no ML, no external services, fully deterministic.

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
  - [Local Setup](#local-setup)
  - [Docker](#docker)
- [Usage](#usage)
  - [CLI](#cli)
  - [Streamlit Web UI](#streamlit-web-ui)
- [Project Structure](#project-structure)
  - [Data Layer (`data/`)](#data-layer-data)
  - [Domain Layer (`domain/`)](#domain-layer-domain)
  - [App Layer (`app/`)](#app-layer-app)
- [How It Works](#how-it-works)
- [Running Tests](#running-tests)
- [Configuration Reference](#configuration-reference)

---

## Overview

Given a seed, number of days, and optional dietary filters, the planner:

1. **Builds meals** by randomly picking foods from required/optional food groups for each meal type (desayuno, almuerzo, merienda, cena).
2. **Validates** each meal against daily constraints (egg, fruit, dairy caps; vegetable minimums), retrying up to 10 times on violations.
3. **Aggregates** all ingredients into a grouped shopping list.

Same seed → same plan, every time.

---

## Quick Start

### Local Setup

**Prerequisites:** Python 3.11+

```bash
# Clone the repo
git clone <repo-url> && cd mealplanner

# Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt

# Generate a 7-day plan
python main.py generate --days 7 --seed 42
```

### Docker

```bash
# Build and generate a plan (CLI, one-shot)
docker compose run cli

# Start the Streamlit web UI on http://localhost:8501
docker compose up web

# Run the test suite
docker compose run --rm tests
```

Or without Compose:

```bash
docker build -t mealplanner .

# CLI
docker run --rm mealplanner generate --days 7 --seed 42

# Streamlit
docker run --rm -p 8501:8501 mealplanner \
  streamlit run app/streamlit_app.py --server.address=0.0.0.0
```

---

## Usage

### CLI

The CLI is powered by [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) and exposes the `generate` command:

```
python main.py generate [OPTIONS]
```

| Option               | Short | Default | Description                                |
| -------------------- | ----- | ------- | ------------------------------------------ |
| `--days`             | `-d`  | `7`     | Number of days to plan                     |
| `--seed`             | `-s`  | `42`    | Random seed for reproducibility            |
| `--vegetarian`       | `-v`  | off     | Exclude animal proteins                    |
| `--exclude`          | `-e`  | —       | Food ID to exclude (repeatable)            |
| `--no-shopping-list` |       | off     | Omit the shopping list from output         |

**Examples:**

```bash
# Basic 7-day plan
python main.py generate

# 5-day vegetarian plan, no salmon or tuna
python main.py generate -d 5 -v --exclude salmon --exclude atun_lata

# Just the plan, skip the shopping list
python main.py generate --no-shopping-list

# Check version
python main.py version
```

### Streamlit Web UI

```bash
streamlit run app/streamlit_app.py
```

Opens a browser UI at `http://localhost:8501` with:

- **Sidebar controls** — day count slider, seed input, vegetarian toggle, food exclusion multi-select.
- **Weekly plan table** — all meals displayed in a dataframe.
- **Shopping list** — items grouped by food category in expandable sections.
- **Recipe details** — expandable cards with ingredients, prep time, and links.

---

## Project Structure

```
mealplanner/
├── main.py                  # Typer CLI entry point (generate, version)
├── pyproject.toml           # Project metadata & build config
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image (CLI + Streamlit)
├── docker-compose.yml       # Services: cli, web, tests
│
├── data/                    # Static JSON data (all in Spanish)
│   ├── foods.json           # 32 food items with grupo, subgrupo, portion, unit
│   ├── groups.json          # 8 food groups mapping to food IDs
│   ├── meal_types.json      # 4 meal types with required/optional groups
│   ├── constraints.json     # Daily/weekly nutritional caps
│   └── recipes.json         # 12 recipes (informational, not used by generator)
│
├── domain/                  # Core business logic (no I/O dependencies)
│   ├── models.py            # Pydantic v2 models + DataLoader
│   ├── rules.py             # RuleEngine — constraint validation & tracking
│   ├── generator.py         # MealGenerator — seeded random plan generation
│   └── shopping.py          # ShoppingListBuilder — quantity aggregation
│
├── app/                     # Presentation layer
│   ├── cli.py               # Typer + Rich CLI command
│   └── streamlit_app.py     # Streamlit web UI
│
└── tests/                   # Pytest test suite
    ├── test_models.py       # DataLoader & model validation
    ├── test_rules.py        # RuleEngine constraint checks
    ├── test_generator.py    # Deterministic generation & dietary filters
    └── test_shopping.py     # Shopping list aggregation & formatting
```

### Data Layer (`data/`)

All data is stored as flat JSON files in Spanish. The `DataLoader` class in `models.py` reads them at startup.

| File                | Contents                                                                 |
| ------------------- | ------------------------------------------------------------------------ |
| `foods.json`        | 32 food items — each has an `id`, `nombre`, `grupo`, `subgrupo`, `porcion_default`, `unidad`, and optional `notas`. |
| `groups.json`       | 8 food groups (`proteinas_animales`, `huevos`, `proteinas_vegetales`, `verduras`, `frutas`, `almidones`, `lacteos`, `grasas_saludables`) — each lists its member food IDs. |
| `meal_types.json`   | 4 meal types — each declares which food groups are **required** (must appear) and **optional** (50% chance). |
| `constraints.json`  | Daily caps: max 2 eggs, max 3 fruits, max 2 dairy, min 2 vegetables; weekly: 1 pizza. |
| `recipes.json`      | 12 recipes with ingredients, prep time, and URLs. Displayed in Streamlit but **not** used by the generator. |

### Domain Layer (`domain/`)

Pure business logic with no framework dependencies.

- **`models.py`** — Pydantic v2 data classes: `FoodItem`, `FoodGroup`, `MealType`, `Constraints`, `Recipe`, `RecipeIngredient`, `MealItem`, `Meal`, `DayPlan`, `WeekPlan`, `ShoppingItem`, `ShoppingList`. Also contains `DataLoader` which reads all JSON files from `data/`.

- **`rules.py`** — `RuleEngine` takes constraints, foods, and groups. It maintains a per-day mutable tracker (`eggs_today`, `fruits_today`, `lacteos_today`, `verduras_today`, `item_counts`) and provides:
  - `validate_meal(meal, tracker)` → checks if adding a meal would exceed daily caps.
  - `update_tracker(meal, tracker)` → commits a meal's items to the tracker.
  - `check_daily_limits(tracker)` → ensures minimums (e.g., vegetables) are met at end of day.

- **`generator.py`** — `MealGenerator` uses a seeded `random.Random` instance. For each day it loops through all 4 meal types, picking one random food from each required group and optionally from each optional group (50% coin flip). If the generated meal violates constraints, it retries up to 10 times (`MAX_RETRIES`), falling back to best-effort. Supports:
  - `vegetarian=True` — filters out all `proteina_animal` foods.
  - `excluded_ids` — arbitrary set of food IDs to never use.

- **`shopping.py`** — `ShoppingListBuilder` walks every `MealItem` in a `WeekPlan`, sums quantities by food ID, and produces a `ShoppingList`. The `format_list()` method renders a human-readable string grouped by food category with emoji headers.

### App Layer (`app/`)

Two independent frontends that both call the same domain logic:

- **`cli.py`** — A single Typer `generate` command. Loads data, builds the generator, prints a Rich table for the weekly plan, and optionally prints the shopping list.
- **`streamlit_app.py`** — Sidebar with sliders/toggles/multi-select, a dataframe view of the plan, expandable shopping list sections, and recipe detail cards.

---

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  DataLoader  │────▶│ MealGenerator│────▶│   WeekPlan   │
│  (JSON → Py) │     │ (seeded RNG) │     │  (7 DayPlans)│
└─────────────┘     └──────┬───────┘     └──────┬───────┘
                           │                     │
                    ┌──────▼───────┐     ┌───────▼──────────┐
                    │  RuleEngine  │     │ShoppingListBuilder│
                    │  (validate)  │     │   (aggregate)     │
                    └──────────────┘     └──────────────────┘
```

1. **Load** — `DataLoader` reads all JSON files into typed Pydantic models.
2. **Generate** — For each day, `MealGenerator` iterates over meal types:
   - Picks a random food from each **required** group.
   - Flips a coin for each **optional** group (50% chance to include).
   - `RuleEngine.validate_meal()` checks constraints; retries up to 10× on failure.
   - `RuleEngine.update_tracker()` commits the accepted meal.
3. **Shop** — `ShoppingListBuilder.build()` sums all `MealItem` quantities across the week into a deduplicated, group-sorted shopping list.
4. **Present** — CLI prints a Rich table + formatted list; Streamlit renders an interactive dashboard.

---

## Running Tests

```bash
# Local
pytest -v

# Docker
docker compose run --rm tests
```

The test suite covers:

| Module               | What's tested                                                        |
| -------------------- | -------------------------------------------------------------------- |
| `test_models.py`     | DataLoader returns correct types; expected food/group IDs exist      |
| `test_rules.py`      | Egg/fruit/dairy cap violations; unknown foods; vegetable minimums; tracker updates |
| `test_generator.py`  | Day count & names; seed reproducibility; vegetarian filtering; food exclusion |
| `test_shopping.py`   | Quantity aggregation; food names & groups; empty plan edge case; formatting |

---

## Configuration Reference

### Adding a new food

1. Add an entry to `data/foods.json`:
   ```json
   {
     "id": "mi_alimento",
     "nombre": "Mi Alimento",
     "grupo": "verdura",
     "subgrupo": "verdura_fresca",
     "porcion_default": 1,
     "unidad": "taza",
     "notas": []
   }
   ```
2. Add the ID to the matching group in `data/groups.json`.

### Adding a new food group

1. Add a new group object to `data/groups.json` with its member food IDs.
2. Reference the group ID in `meal_types.json` under `requires` or `optional` as needed.

### Changing constraints

Edit `data/constraints.json`. Available fields:

| Field                  | Type | Description               |
| ---------------------- | ---- | ------------------------- |
| `max_huevos_por_dia`   | int  | Max eggs per day          |
| `max_frutas_por_dia`   | int  | Max fruit servings/day    |
| `max_lacteos_por_dia`  | int  | Max dairy servings/day    |
| `min_verduras_por_dia` | int  | Min vegetable servings/day|
| `pizza_por_semana`     | int  | Max pizza servings/week   |

### Adding a recipe

Add an object to `data/recipes.json`. Recipes are informational (shown in Streamlit) and do not affect plan generation.

