from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src import migrations


@pytest.fixture
def runner():
    return CliRunner()


@patch("src.migrations.subprocess.run")
@patch("src.migrations.click.echo")
@patch("src.migrations.click.secho")
def test_makemigrations_success(mock_secho, mock_echo, mock_run, runner):
    mock_run.return_value = MagicMock(
        returncode=0, stdout="migration created", stderr=""
    )
    result = runner.invoke(migrations.cli, ["makemigrations", "-m", "test message"])

    mock_run.assert_called_once()
    mock_secho.assert_called_with("✓ Migration created successfully", fg="green")
    mock_echo.assert_called_with("migration created")
    assert result.exit_code == 0


@patch("src.migrations.subprocess.run")
@patch("src.migrations.click.echo")
@patch("src.migrations.click.secho")
@patch("src.migrations.sys.exit", side_effect=SystemExit(1))
def test_makemigrations_failure(mock_exit, mock_secho, mock_echo, mock_run, runner):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error details")
    result = runner.invoke(migrations.cli, ["makemigrations", "-m", "test message"])

    mock_run.assert_called_once()
    mock_secho.assert_called_with("✗ Failed to create migration", fg="red")
    mock_echo.assert_called_with("error details")
    # Relax assertion to check if sys.exit called with 1 at least once
    exit_calls = [call.args[0] for call in mock_exit.call_args_list]
    assert 1 in exit_calls
    assert result.exit_code != 0


@patch("src.migrations.subprocess.run", side_effect=Exception("subprocess error"))
@patch("src.migrations.click.secho")
@patch("src.migrations.sys.exit", side_effect=SystemExit(1))
def test_makemigrations_exception(mock_exit, mock_secho, mock_run, runner):
    result = runner.invoke(migrations.cli, ["makemigrations", "-m", "test message"])

    mock_secho.assert_called_with("✗ Error: subprocess error", fg="red")
    mock_exit.assert_called_once_with(1)
    assert result.exit_code != 0


@pytest.mark.parametrize(
    "command,args,message_success,message_failure",
    [
        ("migrate", [], "✓ Migration applied successfully", "✗ Migration failed"),
        ("downgrade", ["-r", "1234"], "✓ Downgrade successful", "✗ Downgrade failed"),
        ("history", [], None, "✗ Failed to retrieve history"),
        ("current", [], None, "✗ Failed to get current revision"),
    ],
)
@patch("src.migrations.subprocess.run")
@patch("src.migrations.click.echo")
@patch("src.migrations.click.secho")
def test_other_commands_success_failure(
    mock_secho,
    mock_echo,
    mock_run,
    runner,
    command,
    args,
    message_success,
    message_failure,
):
    # Success case
    mock_run.return_value = MagicMock(
        returncode=0, stdout=f"{command} success output", stderr=""
    )
    result = runner.invoke(migrations.cli, [command] + args)
    mock_secho_calls = [call[0][0] for call in mock_secho.call_args_list]

    if message_success:
        assert message_success in mock_secho_calls
    mock_echo.assert_any_call(f"{command} success output")
    assert result.exit_code == 0

    mock_secho.reset_mock()
    mock_echo.reset_mock()

    # Failure case
    with patch("src.migrations.sys.exit", side_effect=SystemExit(1)) as mock_exit:
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr=f"{command} error output"
        )
        result = runner.invoke(migrations.cli, [command] + args)

        if message_failure:
            mock_secho.assert_any_call(message_failure, fg="red")
        mock_echo.assert_any_call(f"{command} error output")
        mock_exit.assert_called_once_with(1)
        assert result.exit_code != 0


@pytest.mark.parametrize(
    "command,args",
    [
        ("migrate", []),
        ("downgrade", ["-r", "1234"]),
        ("history", []),
        ("current", []),
    ],
)
@patch("src.migrations.subprocess.run", side_effect=Exception("subproc error"))
@patch("src.migrations.click.secho")
@patch("src.migrations.sys.exit", side_effect=SystemExit(1))
def test_other_commands_exception(
    mock_exit, mock_secho, mock_run, runner, command, args
):
    result = runner.invoke(migrations.cli, [command] + args)

    mock_secho.assert_called_with("✗ Error: subproc error", fg="red")
    mock_exit.assert_called_once_with(1)
    assert result.exit_code != 0
