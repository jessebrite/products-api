import logging
from unittest.mock import ANY, Mock, patch

from fastapi import HTTPException

from src.logger import (
    _get_log_context,
    log_response,
    logger,
    setup_logger,
)


class TestSetupLogger:
    def test_setup_logger_creates_handler_once(self):
        """Test that setup_logger adds handler only once."""
        # Clear existing handlers
        logger.handlers.clear()
        setup_logger()
        initial_count = len(logger.handlers)
        setup_logger()  # Call again
        assert len(logger.handlers) == initial_count

    def test_setup_logger_sets_level(self):
        """Test that logger level is set to INFO."""
        setup_logger()
        assert logger.level == logging.INFO


class TestGetLogContext:
    def test_get_log_context_basic(self):
        """Test basic log context creation."""
        request = Mock()
        request.method = "GET"
        request.url.path = "/test"
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-agent"}
        request.state = Mock()
        request.state.request_id = "test-id"

        context = _get_log_context(request, 200)
        assert context["method"] == "GET"
        assert context["path"] == "/test"
        assert context["status_code"] == 200
        assert context["ip"] == "127.0.0.1"
        assert context["user_agent"] == "test-agent"
        assert context["request_id"] == "test-id"

    def test_get_log_context_with_user(self):
        """Test log context with user in request state."""
        request = Mock()
        request.method = "POST"
        request.url.path = "/user"
        request.client.host = "192.168.1.1"
        request.headers = {"user-agent": "browser"}
        request.state = Mock()
        request.state.request_id = "req-123"
        request.state.user = Mock()
        request.state.user.id = 42

        context = _get_log_context(request, 201)
        assert context["user_id"] == 42

    def test_get_log_context_no_user(self):
        """Test log context without user."""
        request = Mock()
        request.method = "DELETE"
        request.url.path = "/item"
        request.client.host = "10.0.0.1"
        request.headers = {"user-agent": "api-client"}
        request.state = Mock()

        context = _get_log_context(request, 204)
        assert context["user_id"] is None

    def test_get_log_context_with_detail_and_body(self):
        """Test log context with detail and response body."""
        request = Mock()
        request.method = "PUT"
        request.url.path = "/update"
        request.client.host = "localhost"
        request.headers = {"user-agent": "test"}
        request.state = Mock()
        request.state.request_id = "put-req"

        context = _get_log_context(
            request, 400, detail="Bad input", response_body={"error": "invalid"}
        )
        assert context["detail"] == "Bad input"
        assert context["response_body"] == {"error": "invalid"}


class TestLogException:
    def test_log_response_server_error(self):
        """Test logging server errors (5xx)."""
        request = Mock()
        exc = HTTPException(status_code=500, detail="Internal error")

        with patch.object(logger, "error") as mock_error:
            log_response(request, exc)
            mock_error.assert_called_once()
            args, kwargs = mock_error.call_args
            assert "Server error: 500" in args[0]

    def test_log_response_bad_request(self):
        """Test logging 400 Bad Request."""
        request = Mock()
        exc = HTTPException(status_code=400, detail="Bad request")

        with patch.object(logger, "error") as mock_error:
            log_response(request, exc)
            mock_error.assert_called_once_with("Bad Request: 400", extra=ANY)

    def test_log_response_unauthorized(self):
        """Test logging 401 Unauthorized."""
        request = Mock()
        exc = HTTPException(status_code=401, detail="Unauthorized")

        with patch.object(logger, "error") as mock_error:
            log_response(request, exc)
            mock_error.assert_called_once_with("Unauthorized: 401", extra=ANY)

    def test_log_response_not_found(self):
        """Test logging 404 Not Found."""
        request = Mock()
        exc = HTTPException(status_code=404, detail="Not found")

        with patch.object(logger, "error") as mock_info:
            log_response(request, exc)
            mock_info.assert_called_once_with("Not found: 404", extra=ANY)

    def test_log_response_conflict(self):
        """Test logging 409 Conflict."""
        request = Mock()
        exc = HTTPException(status_code=409, detail="Conflict")

        with patch.object(logger, "error") as mock_info:
            log_response(request, exc)
            mock_info.assert_called_once_with("Conflict: 409", extra=ANY)

    def test_log_response_forbidden(self):
        """Test logging 403 Forbidden (catch-all client error)."""
        request = Mock()
        exc = HTTPException(status_code=403, detail="Forbidden")

        with patch.object(logger, "error") as mock_info:
            log_response(request, exc)
            mock_info.assert_called_once_with("Client error: 403", extra=ANY)

    def test_log_response_success_status(self):
        """Test logging with success status codes."""
        request = Mock()
        status_code: str = 200

        with patch.object(logger, "info") as mock_info:
            log_response(request, status_code=status_code)
            mock_info.assert_called_once_with("Request succeeded: 200", extra=ANY)


class TestLogSuccess:
    def test_log_response_success_basic(self):
        """Test logging successful response."""
        request = Mock()
        status_code = 200

        with patch.object(logger, "info") as mock_info:
            log_response(request, status_code=status_code)
            mock_info.assert_called_once_with("Request succeeded: 200", extra=ANY)

    def test_log_response_success_with_body(self):
        """Test logging successful response with body."""
        request = Mock()
        status_code = 201
        response_body = {"id": 1}

        with patch.object(logger, "info") as mock_info:
            log_response(request, response_body=response_body, status_code=status_code)
            mock_info.assert_called_once_with("Request succeeded: 201", extra=ANY)
            extra = mock_info.call_args[1]["extra"]
            assert extra["response_body"] == response_body
