"""Database migration management CLI."""

import subprocess
import sys
from pathlib import Path

import click


@click.group()
def cli():
    """Database migration management commands."""
    pass


@cli.command()
@click.option("--message", "-m", required=True, help="Migration description")
def makemigrations(message: str):
    """Create a new migration file."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alembic",
                "revision",
                "--autogenerate",
                "-m",
                message,
            ],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            click.secho("✓ Migration created successfully", fg="green")
            click.echo(result.stdout)
        else:
            click.secho("✗ Failed to create migration", fg="red")
            click.echo(result.stderr)
            sys.exit(1)
    except Exception as e:
        click.secho(f"✗ Error: {str(e)}", fg="red")
        sys.exit(1)


@cli.command()
@click.option(
    "--revision", "-r", default="head", help="Target revision (default: head)"
)
def migrate(revision: str):
    """Apply migrations to the database."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", revision],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            click.secho("✓ Migration applied successfully", fg="green")
            click.echo(result.stdout)
        else:
            click.secho("✗ Migration failed", fg="red")
            click.echo(result.stderr)
            sys.exit(1)
    except Exception as e:
        click.secho(f"✗ Error: {str(e)}", fg="red")
        sys.exit(1)


@cli.command()
@click.option("--revision", "-r", required=True, help="Target revision to downgrade to")
def downgrade(revision: str):
    """Downgrade to a specific migration."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", revision],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            click.secho("✓ Downgrade successful", fg="green")
            click.echo(result.stdout)
        else:
            click.secho("✗ Downgrade failed", fg="red")
            click.echo(result.stderr)
            sys.exit(1)
    except Exception as e:
        click.secho(f"✗ Error: {str(e)}", fg="red")
        sys.exit(1)


@cli.command()
def history():
    """Show migration history."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "history"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            click.echo(result.stdout)
        else:
            click.secho("✗ Failed to retrieve history", fg="red")
            click.echo(result.stderr)
            sys.exit(1)
    except Exception as e:
        click.secho(f"✗ Error: {str(e)}", fg="red")
        sys.exit(1)


@cli.command()
def current():
    """Show current database revision."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "current"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            click.echo(result.stdout)
        else:
            click.secho("✗ Failed to get current revision", fg="red")
            click.echo(result.stderr)
            sys.exit(1)
    except Exception as e:
        click.secho(f"✗ Error: {str(e)}", fg="red")
        sys.exit(1)


if __name__ == "__main__":
    cli()
