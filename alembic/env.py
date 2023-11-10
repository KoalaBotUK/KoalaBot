import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# Config Path
CONFIG_PATH = os.environ.get("CONFIG_PATH")

if not CONFIG_PATH:
    CONFIG_PATH = "/config"
    if os.name == 'nt':
        CONFIG_PATH = '.'+CONFIG_PATH
CONFIG_PATH = Path(CONFIG_PATH)
CONFIG_PATH.mkdir(exist_ok=True, parents=True)

# Database
DB_URL = os.environ.get("DB_URL")

if not DB_URL:
    # Use SQLite
    ENCRYPTED_DB = (not os.name == 'nt') and eval(os.environ.get('ENCRYPTED', "True"))
    DB_KEY = os.environ.get('SQLITE_KEY', "2DD29CA851E7B56E4697B0E1F08507293D761A05CE4D1B628663F411A8086D99")
    SQLITE_DB_PATH = Path(CONFIG_PATH, "Koala.db" if ENCRYPTED_DB else "windows_Koala.db")
    SQLITE_DB_PATH.touch()
    if ENCRYPTED_DB:
        os.system(f"chown www-data {CONFIG_PATH.absolute()}")
        os.system(f"chmod 777 {CONFIG_PATH}")
        DB_URL = f"sqlite+pysqlcipher://:x'{DB_KEY}'@/{SQLITE_DB_PATH.absolute()}?charset=utf8mb4"
    else:
        DB_URL = f"sqlite:///{SQLITE_DB_PATH.absolute()}?charset=utf8mb4"

config.set_main_option('sqlalchemy.url', DB_URL)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
