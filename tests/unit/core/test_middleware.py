from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

from src.core.middleware import (
    LoggingMiddleware,
    RequestIDMiddleware,
    RequestSizeLimiter,
    SecurityHeadersMiddleware,
)


class AsyncIteratorMock:
    def __init__(self, chunks):
        self.chunks = chunks
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.chunks):
            raise StopAsyncIteration
        chunk = self.chunks[self.index]
        self.index += 1
        return chunk


class TestLoggingMiddleware:
    @pytest.mark.asyncio
    async def test_dispatch_successful_response(self):
        """Test middleware logs successful responses."""
        middleware = LoggingMiddleware(Mock())
        request = Mock()
        response = Mock()
        response.status_code = 200

        call_next = AsyncMock(return_value=response)

        with patch("src.core.middleware.log_success") as mock_log_success:
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


class TestRequestSizeLimiter:
    @pytest.mark.asyncio
    async def test_dispatch_non_body_method(self):
        """Test middleware skips size check for non-body methods."""
        middleware = RequestSizeLimiter(Mock(), max_size=100)
        request = Mock()
        request.method = "GET"
        response = Mock()

        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)
        assert result == response

    @pytest.mark.asyncio
    async def test_dispatch_content_length_exceeds(self):
        """Test middleware raises exception for large Content-Length."""
        middleware = RequestSizeLimiter(Mock(), max_size=100)
        request = Mock()
        request.method = "POST"
        request.headers = {"content-length": "200"}

        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)
        assert exc_info.value.status_code == 413
        assert "Request body too large. Max size: 100 bytes." in exc_info.value.detail
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_content_length_within_limit(self):
        """Test middleware proceeds for Content-Length within limit."""
        middleware = RequestSizeLimiter(Mock(), max_size=100)
        request = Mock()
        request.method = "POST"
        request.headers = {"content-length": "50"}

        async def fake_stream():
            yield b"small body under limit"

        request.stream = lambda: fake_stream()
        request.scope = {}

        call_next = AsyncMock()

        result = await middleware.dispatch(request, call_next)
        assert request._body == b"small body under limit"
        assert request.scope["body"] == b"small body under limit"
        call_next.assert_called_once_with(request)
        assert result == call_next.return_value

    @pytest.mark.asyncio
    async def test_dispatch_chunked_body_exceeds(self):
        """Test middleware raises exception for large chunked body."""
        middleware = RequestSizeLimiter(Mock(), max_size=10)
        request = Mock()
        request.method = "POST"
        request.headers = {}

        async def fake_stream():
            yield b"small body under limit"

        request.stream = lambda: fake_stream()
        request.scope = {}

        call_next = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)
        assert exc_info.value.status_code == 413
        assert "Request body too large." in str(exc_info.value.detail)
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_chunked_body_within_limit(self):
        """Test middleware proceeds for chunked body within limit."""
        middleware = RequestSizeLimiter(Mock(), max_size=20)
        request = Mock()
        request.method = "POST"
        request.headers = {}

        async def fake_stream():
            yield b"small body under limit"

        request.stream = lambda: fake_stream()

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, Mock())
        assert exc_info.value.status_code == 413


class TestSecurityHeadersMiddleware:
    @pytest.mark.asyncio
    async def test_dispatch_adds_security_headers(self):
        """Test middleware adds security headers to response."""
        middleware = SecurityHeadersMiddleware(Mock())
        request = Mock()
        response = Mock()
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        assert result == response
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"


class TestRequestIDMiddleware:
    @pytest.mark.asyncio
    async def test_dispatch_with_existing_request_id(self):
        """Test middleware uses existing X-Request-ID."""
        middleware = RequestIDMiddleware(Mock())
        request = Mock()
        request.headers = {"X-Request-ID": "existing-id"}
        request.state = Mock()
        response = Mock()
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)
        assert result == response
        assert request.state.request_id == "existing-id"
        assert response.headers["X-Request-ID"] == "existing-id"

    @pytest.mark.asyncio
    async def test_dispatch_generates_new_request_id(self):
        """Test middleware generates new UUID if no X-Request-ID."""
        middleware = RequestIDMiddleware(Mock())
        request = Mock()
        request.headers = {}
        request.state = Mock()
        response = Mock()
        response.headers = {}

        call_next = AsyncMock(return_value=response)

        mock_uuid_obj = Mock()
        mock_uuid_obj.hex = "generated-uuid"
        mock_uuid_obj.__str__ = Mock(return_value="generated-uuid")
        with patch(
            "src.core.middleware.uuid.uuid4", return_value=mock_uuid_obj
        ) as mock_uuid:
            result = await middleware.dispatch(request, call_next)
            mock_uuid.assert_called_once()
            assert result == response
            assert request.state.request_id == "generated-uuid"
            assert response.headers["X-Request-ID"] == "generated-uuid"
