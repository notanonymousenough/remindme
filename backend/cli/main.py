import click
from backend.cli.commands.sync_types import sync_types

@click.group()
def cli():
    """Утилиты управления для backend."""
    pass

# Регистрируем команду
cli.add_command(sync_types)

if __name__ == "__main__":
    cli()
