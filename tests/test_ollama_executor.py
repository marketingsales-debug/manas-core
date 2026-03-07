"""Tests for OllamaExecutor."""

import pytest
from unittest.mock import patch, MagicMock
from src.executor.ollama import OllamaExecutor


class TestOllamaExecutor:
    def test_init_defaults(self):
        executor = OllamaExecutor()
        assert executor.base_url == "http://localhost:11434"
        assert executor.model == "llama3.1"
        assert executor.generation_count == 0

    def test_health_check_success(self):
        executor = OllamaExecutor()
        with patch.object(executor.session, "get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            assert executor._check_health() is True

    def test_health_check_failure(self):
        executor = OllamaExecutor()
        with patch.object(executor.session, "get") as mock_get:
            import requests
            mock_get.side_effect = requests.ConnectionError()
            assert executor._check_health() is False

    def test_is_available_caches(self):
        executor = OllamaExecutor()
        with patch.object(executor, "_check_health", return_value=True) as mock:
            assert executor.is_available() is True
            assert executor.is_available() is True
            # Should only call health check once (cached)
            assert mock.call_count == 1

    def test_generate_success(self):
        executor = OllamaExecutor()
        executor._available = True
        executor._last_health_check = 9999999999.0  # far future

        with patch.object(executor.session, "post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"response": "Hello there!"},
            )
            result = executor.generate("You are helpful", "Hi")
            assert result == "Hello there!"
            assert executor.generation_count == 1

    def test_generate_returns_none_on_connection_error(self):
        executor = OllamaExecutor()
        executor._available = True
        executor._last_health_check = 9999999999.0

        with patch.object(executor.session, "post") as mock_post:
            import requests
            mock_post.side_effect = requests.ConnectionError()
            result = executor.generate("system", "user")
            assert result is None
            assert executor._available is False

    def test_generate_returns_none_when_unavailable(self):
        executor = OllamaExecutor()
        executor._available = False
        executor._last_health_check = 9999999999.0
        result = executor.generate("system", "user")
        assert result is None

    def test_get_stats(self):
        executor = OllamaExecutor()
        executor._available = True
        executor._last_health_check = 9999999999.0
        stats = executor.get_stats()
        assert stats["model"] == "llama3.1"
        assert stats["generations"] == 0
