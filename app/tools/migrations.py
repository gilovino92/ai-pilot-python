import os
import sys
import argparse
from pathlib import Path
from alembic.config import Config
from alembic import command

def get_alembic_config():
    """Get the Alembic configuration."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    # Path to alembic.ini
    alembic_ini = project_root / "alembic.ini"
    # Create Alembic config
    config = Config(str(alembic_ini))
    # Set the script location
    config.set_main_option("script_location", str(project_root / "alembic"))
    return config

def create_migration(message: str):
    """Create a new migration with autogenerate."""
    config = get_alembic_config()
    command.revision(config, message=message, autogenerate=True)

def upgrade_database(revision: str = "head"):
    """Upgrade the database to the specified revision."""
    config = get_alembic_config()
    command.upgrade(config, revision)

def downgrade_database(revision: str = "-1"):
    """Downgrade the database by one version."""
    config = get_alembic_config()
    command.downgrade(config, revision)

def show_current_version():
    """Show the current database version."""
    config = get_alembic_config()
    command.current(config)

def show_migration_history():
    """Show the migration history."""
    config = get_alembic_config()
    command.history(config)

def main():
    parser = argparse.ArgumentParser(description='Database migration commands')
    subparsers = parser.add_subparsers(dest='command', help='Migration command to run')

    # Create migration command
    create_parser = subparsers.add_parser('create', help='Create a new migration')
    create_parser.add_argument('message', help='Migration message')

    # Upgrade command
    upgrade_parser = subparsers.add_parser('upgrade', help='Upgrade database')
    upgrade_parser.add_argument('--revision', default='head', help='Revision to upgrade to')

    # Downgrade command
    downgrade_parser = subparsers.add_parser('downgrade', help='Downgrade database')
    downgrade_parser.add_argument('--revision', default='-1', help='Revision to downgrade to')

    # Current version command
    subparsers.add_parser('current', help='Show current version')

    # History command
    subparsers.add_parser('history', help='Show migration history')

    args = parser.parse_args()

    if args.command == 'create':
        create_migration(args.message)
    elif args.command == 'upgrade':
        upgrade_database(args.revision)
    elif args.command == 'downgrade':
        downgrade_database(args.revision)
    elif args.command == 'current':
        show_current_version()
    elif args.command == 'history':
        show_migration_history()
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 