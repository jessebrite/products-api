from unittest.mock import MagicMock, patch

import pytest
from fastapi.responses import JSONResponse

from src.utils import _check_database, health_check, liveness


def test_liveness_returns_json_response():
    response: JSONResponse = liveness()
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    assert response.body == b'{"status":"ok"}'


@pytest.mark.asyncio
@patch("src.utils.SessionLocal")
async def test_check_database_success(mock_session_local):
    mock_db: MagicMock = MagicMock()
    mock_session_local.return_value = mock_db

    result: bool = await _check_database()
    assert result is True
    mock_db.execute.assert_called_once()
    mock_db.close.assert_called_once()


@pytest.mark.asyncio
@patch("src.utils.SessionLocal")
async def test_check_database_failure(mock_session_local):
    mock_db: MagicMock = MagicMock()
    mock_db.execute.side_effect = Exception("DB error")
    mock_session_local.return_value = mock_db

    with patch("src.utils.logger") as mock_logger:
        result = await _check_database()
        assert result is False
        mock_logger.error.assert_called_once_with(
            "Database health check failed: DB error"
        )


@pytest.mark.asyncio
@patch("src.utils._check_database")
async def test_health_check(mock_check_db):
    mock_check_db.return_value = True

    result = await health_check()
    expected = {"database": True}
    assert result == expected
    mock_check_db.assert_called_once()
