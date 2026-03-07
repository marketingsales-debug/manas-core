import pytest
from unittest.mock import patch, MagicMock
from src.executor.llm_router import LLMRouter


@pytest.fixture
def router():
    # Use an invalid config path to force default empty/local config
    router = LLMRouter("invalid_path.json")
    return router


def test_router_initialization(router):
    assert router.config["default_local"]["provider"] == "ollama"
    assert "groq" in router.provider_failures
    assert "anthropic" in router.provider_failures


@patch("src.executor.llm_router.requests.post")
def test_ollama_fallback(mock_post, router):
    # Mock a successful Ollama response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "Hello from local Ollama!"}
    mock_post.return_value = mock_resp

    # With no API keys, simple tasks should route to Ollama
    result = router.generate("Say hello", task_type="simple")
    
    assert "Hello from local Ollama!" in result
    mock_post.assert_called_once()
    
    # Verify timeout parameter
    args, kwargs = mock_post.call_args
    assert kwargs.get("timeout") == 120


@patch("src.executor.llm_router.requests.post")
def test_ollama_failure_increment(mock_post, router):
    # Mock a failed Ollama response
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_post.return_value = mock_resp

    result = router.generate("Say hello", task_type="simple")
    
    assert "Ollama Error" in result
    assert router.provider_failures["ollama"] == 1


# If we had api keys configured in the mock, we could test groq/anthropic routing, 
# but for basic validation we just ensure the router defaults back to ollama if 
# clients are None.
def test_coding_fallback_to_ollama(router):
    with patch.object(router, "_call_ollama", return_value="Local Code") as mock_ollama:
        # Since we have no API keys configured in the fixture, 
        # a coding task should fall all the way through to Ollama fallback.
        result = router.generate("write a python script", task_type="coding")
        assert result == "Local Code"
        mock_ollama.assert_called_once()
