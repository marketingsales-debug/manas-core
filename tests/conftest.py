"""Shared test fixtures for Project Manas."""

import tempfile
import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def tmp_data_dir():
    """Temporary data directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_neurochem():
    """Create a real NeurochemicalSystem for testing."""
    from src.neurotransmitters.chemistry import NeurochemicalSystem
    return NeurochemicalSystem()
