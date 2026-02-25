"""Entry point for the mealplanner CLI."""
import sys
from pathlib import Path

# Ensure project root is on sys.path so domain/app imports work
sys.path.insert(0, str(Path(__file__).parent))

import typer
from app.cli import generate

# Top-level app with an explicit 'generate' subcommand so users can call:
#   python main.py generate --days 7 --seed 42
app = typer.Typer(help="Generador de planes de comida semanal")
app.command("generate")(generate)


@app.command("version")
def version():
    """Show the application version."""
    typer.echo("mealplanner 0.1.0")


if __name__ == "__main__":
    app()
