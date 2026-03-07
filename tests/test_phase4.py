import pytest
import os
from unittest.mock import MagicMock, patch
from src.agents.base import AgentResult
from src.agents.orchestrator import OrchestratorAgent
from src.agents.coder import CoderAgent
from src.cognition.meta_learning import MetaLearningSystem


def test_orchestrator_initialization():
    memory_mock = MagicMock()
    llm_mock = MagicMock()
    
    orchestrator = OrchestratorAgent("Orch", llm_router=llm_mock, memory=memory_mock)
    assert orchestrator.name == "Orch"
    assert orchestrator.status == "idle"


def test_orchestrator_delegation():
    llm_mock = MagicMock()
    # Return a mocked plan to delegate to a researcher
    llm_mock.generate.return_value = '{"steps": [{"agent": "Researcher", "instruction": "Test search"}]}'
    
    orchestrator = OrchestratorAgent("Orch", llm_router=llm_mock)
    
    # Mock Researcher
    researcher_mock = MagicMock()
    researcher_mock.name = "Researcher"
    researcher_mock.run.return_value = AgentResult(True, "Search ok", "logs")
    
    orchestrator.register_agents({"Researcher": researcher_mock})
    
    result = orchestrator.run("Do a search task")
    
    assert result.success is True
    researcher_mock.run.assert_called_once()
    assert "Test search" in researcher_mock.run.call_args[0][0]


def test_coder_agent_loop_success():
    llm_mock = MagicMock()
    # Mock an LLM that immediately returns "done"
    llm_mock.generate.return_value = '{"thought": "I am done", "tool": "", "args": "", "done": true}'
    
    coder = CoderAgent("Coder", llm_router=llm_mock)
    result = coder.run("Write a script")
    
    assert result.success is True
    assert result.output == "I am done"
    assert "Task marked as COMPLETED" in '\n'.join(coder.logs)


def test_coder_agent_tool_execution():
    llm_mock = MagicMock()
    # First iteration: run a bash command. Second: done
    llm_mock.generate.side_effect = [
        '{"thought": "Running bash", "tool": "bash", "args": "echo hello", "done": false}',
        '{"thought": "Done", "tool": "", "args": "", "done": true}'
    ]
    
    coder = CoderAgent("Coder", llm_router=llm_mock)
    
    with patch.object(coder.dispatcher, 'dispatch') as mock_dispatch:
        mock_dispatch.return_value = {"success": True, "output": "hello", "data": {}}
        
        result = coder.run("Say hello")
        
        assert result.success is True
        assert mock_dispatch.call_count == 1
        assert mock_dispatch.call_args[0][0] == "bash: echo hello"


def test_meta_learning_ab_test():
    # Use a temporary file for tests
    mls = MetaLearningSystem(data_dir="/tmp/manas_test_data")
    
    # Check default
    assert mls.get_param("sleep_debt_decay") == 0.05
    
    # Start experiment
    started = mls.start_ab_test("sleep_debt_decay", 0.1, duration_hours=1)
    assert started is True
    assert mls.active_experiment is not None
    assert mls.get_param("sleep_debt_decay") == 0.1
    
    # Record some good metrics (score 1.0 against baseline 0.5)
    mls.record_metric_event(1.0)
    mls.record_metric_event(1.0)
    
    # Force conclude
    mls.conclude_ab_test()
    
    assert mls.active_experiment is None
    # Won the test, should keep the variant
    assert mls.get_param("sleep_debt_decay") == 0.1

    # Clean up test files
    if os.path.exists(mls.params_file): os.remove(mls.params_file)
    if os.path.exists(mls.metrics_file): os.remove(mls.metrics_file)
