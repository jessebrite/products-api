import logging
from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest

from src.logger import (
    LoggingMiddleware,
    _get_log_context,
    log_exception,
    log_success,
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
        # No user attribute

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


class TestLoggingMiddleware:
    @pytest.mark.asyncio
    async def test_dispatch_successful_response(self):
        """Test middleware logs successful responses."""
        middleware = LoggingMiddleware(Mock())
        request = Mock()
        response = Mock()
        response.status_code = 200

        call_next = AsyncMock(return_value=response)

        with patch("src.logger.log_success") as mock_log_success:
            result = await middleware.dispatch(request, call_next)
            mock_log_success.assert_called_once_with(request, 200)
            assert result == response

    @pytest.mark.asyncio
    async def test_dispatch_error_response_no_log(self):
        """Test middleware does not log error responses."""
        middleware = LoggingMiddleware(Mock())
        request = Mock()
        response = Mock()
        response.status_code = 404

        call_next = AsyncMock(return_value=response)

        with patch("src.logger.log_success") as mock_log_success:
            result = await middleware.dispatch(request, call_next)
            mock_log_success.assert_not_called()
            assert result == response


class TestLogException:
    def test_log_exception_server_error(self):
        """Test logging server errors (5xx)."""
        request = Mock()
        exc = Mock()
        exc.status_code = 500
        exc.detail = "Internal error"

        with patch.object(logger, "error") as mock_error:
            log_exception(request, exc)
            mock_error.assert_called_once()
            args, kwargs = mock_error.call_args
            assert "Server error: 500" in args[0]
            assert kwargs["exc_info"] is True

    def test_log_exception_bad_request(self):
        """Test logging 400 Bad Request."""
        request = Mock()
        exc = Mock()
        exc.status_code = 400
        exc.detail = "Bad request"

        with patch.object(logger, "error") as mock_error:
            log_exception(request, exc)
            mock_error.assert_called_once_with("Bad Request", extra=ANY)

    def test_log_exception_unauthorized(self):
        """Test logging 401 Unauthorized."""
        request = Mock()
        exc = Mock()
        exc.status_code = 401
        exc.detail = "Unauthorized"

        with patch.object(logger, "warning") as mock_warning:
            log_exception(request, exc)
            mock_warning.assert_called_once_with("Client error: 401", extra=ANY)

    def test_log_exception_other_client_error(self):
        """Test logging other 4xx errors."""
        request = Mock()
        exc = Mock()
        exc.status_code = 404
        exc.detail = "Not found"

        with patch.object(logger, "info") as mock_info:
            log_exception(request, exc)
            mock_info.assert_called_once_with("Client error: 404", extra=ANY)

    def test_log_exception_success_status(self):
        """Test logging with success status codes."""
        request = Mock()
        exc = Mock()
        exc.status_code = 200
        exc.detail = "OK"

        with patch.object(logger, "info") as mock_info:
            log_exception(request, exc)
            mock_info.assert_called_once_with("Request succeeded", extra=ANY)


class TestLogSuccess:
    def test_log_success_basic(self):
        """Test logging successful response."""
        request = Mock()
        status_code = 200

        with patch.object(logger, "info") as mock_info:
            log_success(request, status_code)
            mock_info.assert_called_once_with("Request succeeded", extra=ANY)

    def test_log_success_with_body(self):
        """Test logging successful response with body."""
        request = Mock()
        status_code = 201
        response_body = {"id": 1}

        with patch.object(logger, "info") as mock_info:
            log_success(request, status_code, response_body)
            mock_info.assert_called_once_with("Request succeeded", extra=ANY)
            # Check that response_body is in the extra dict
            extra = mock_info.call_args[1]["extra"]
            assert extra["response_body"] == response_body
