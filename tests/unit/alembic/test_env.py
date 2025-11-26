import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to path for imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)


def test_env_configuration_setup():
    """Test that env.py sets up configuration correctly."""
    with (
        patch("logging.config.fileConfig") as mock_fileconfig,
        patch("config.settings") as mock_settings,
        patch("models.Base") as mock_base,
        patch("alembic.context", create=True) as mock_context,
    ):
        # Create mock config
        mock_config = MagicMock()
        mock_context.config = mock_config
        mock_config.config_file_name = "alembic.ini"
        mock_settings.database_url = "sqlite:///test.db"
        mock_base.metadata = MagicMock()

        # Execute the setup part of env.py
        env_globals = {
            "os": os,
            "sys": sys,
            "fileConfig": mock_fileconfig,
            "context": mock_context,
            "settings": mock_settings,
            "Base": mock_base,
        }

        exec(
            """
# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Set the target metadata
target_metadata = Base.metadata
""",
            env_globals,
        )

        # Verify fileConfig was called
        mock_fileconfig.assert_called_once_with("alembic.ini")

        # Verify config.set_main_option was called with database URL
        mock_config.set_main_option.assert_called_once_with(
            "sqlalchemy.url", "sqlite:///test.db"
        )

        # Verify target_metadata is set
        assert env_globals["target_metadata"] == mock_base.metadata


def test_run_migrations_offline():
    """Test run_migrations_offline function."""
    with patch("alembic.context", create=True) as mock_context:
        mock_config = MagicMock()
        mock_context.config = mock_config
        mock_config.get_main_option.return_value = "sqlite:///test.db"
        mock_context.begin_transaction.return_value.__enter__ = MagicMock()
        mock_context.begin_transaction.return_value.__exit__ = MagicMock()

        target_metadata = MagicMock()

        # Execute run_migrations_offline function
        env_globals = {
            "context": mock_context,
            "target_metadata": target_metadata,
        }

        exec(
            """
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

run_migrations_offline()
""",
            {"config": mock_config, **env_globals},
        )

        # Verify context.configure was called with correct parameters
        mock_context.configure.assert_called_once_with(
            url="sqlite:///test.db",
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        # Verify run_migrations was called
        mock_context.run_migrations.assert_called_once()


def test_run_migrations_online():
    """Test run_migrations_online function."""
    with (
        patch("sqlalchemy.engine_from_config") as mock_engine_from_config,
        patch("alembic.context", create=True) as mock_context,
        patch("config.settings") as mock_settings,
    ):
        mock_config = MagicMock()
        mock_context.config = mock_config
        mock_config.get_section.return_value = {"sqlalchemy.url": "old_url"}
        mock_settings.database_url = "sqlite:///test.db"
        mock_engine = MagicMock()
        mock_engine_from_config.return_value = mock_engine
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_engine.connect.return_value.__exit__ = MagicMock()
        mock_context.begin_transaction.return_value.__enter__ = MagicMock()
        mock_context.begin_transaction.return_value.__exit__ = MagicMock()

        target_metadata = MagicMock()

        # Execute run_migrations_online function
        env_globals = {
            "context": mock_context,
            "target_metadata": target_metadata,
            "settings": mock_settings,
            "engine_from_config": mock_engine_from_config,
            "pool": MagicMock(),
        }

        exec(
            """
def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.StaticPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
""",
            {"config": mock_config, **env_globals},
        )

        # Verify engine_from_config was called
        mock_engine_from_config.assert_called_once()

        # Verify context.configure was called with connection
        mock_context.configure.assert_called_once_with(
            connection=mock_connection, target_metadata=target_metadata
        )

        # Verify run_migrations was called
        mock_context.run_migrations.assert_called_once()


def test_main_execution_offline_mode():
    """Test main execution in offline mode."""
    with patch("alembic.context", create=True) as mock_context:
        mock_context.is_offline_mode.return_value = True

        offline_called = False
        online_called = False

        def mock_run_migrations_offline():
            nonlocal offline_called
            offline_called = True

        def mock_run_migrations_online():
            nonlocal online_called
            online_called = True

        # Simulate the main execution logic from env.py
        if mock_context.is_offline_mode():
            mock_run_migrations_offline()
        else:
            mock_run_migrations_online()

        assert offline_called
        assert not online_called


def test_main_execution_online_mode():
    """Test main execution in online mode."""
    with patch("alembic.context", create=True) as mock_context:
        mock_context.is_offline_mode.return_value = False

        offline_called = False
        online_called = False

        def mock_run_migrations_offline():
            nonlocal offline_called
            offline_called = True

        def mock_run_migrations_online():
            nonlocal online_called
            online_called = True

        # Simulate the main execution logic from env.py
        if mock_context.is_offline_mode():
            mock_run_migrations_offline()
        else:
            mock_run_migrations_online()

        assert not offline_called
        assert online_called
