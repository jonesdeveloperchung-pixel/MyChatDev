"""Unit tests for QualityGate functionality.

Author: Jones Chung
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from config.settings import LLMConfig, SystemConfig, AVAILABLE_LLMS
from models.llm_manager import LLMManager
from workflow.quality_gate import QualityGate
from utils.prompts import get_prompt


class TestQualityGate:
    """Test cases for QualityGate."""

    @pytest.fixture
    def system_config(self):
        """Sample system configuration for testing."""
        return SystemConfig(
            ollama_host="http://localhost:11434",
            max_iterations=3,
            quality_threshold=0.8,
            change_threshold=0.1,
            enable_compression=False, # Disable compression for simpler testing
        )

    @pytest.fixture
    def llm_configs(self):
        """Sample LLM configurations for testing."""
        return AVAILABLE_LLMS

    @pytest.fixture
    def llm_manager(self, system_config):
        """LLM Manager instance for testing."""
        return LLMManager(system_config)

    @pytest.fixture
    def quality_gate(self, llm_manager, llm_configs, system_config):
        """QualityGate instance for testing."""
        return QualityGate(
            llm_manager,
            llm_configs["quality_gate"],
            system_config.quality_threshold,
            system_config.change_threshold,
        )

    @pytest.mark.asyncio
    async def test_evaluate_state_halt_quality_met(self, quality_gate, llm_manager):
        """Test evaluate_state halts when quality threshold is met."""
        current_state = {'requirements': 'req', 'design': 'design', 'code': 'code'}
        previous_state = None
        
        mock_response = MagicMock()
        mock_response.tool_calls = None
        mock_response.content = "'overall_quality_score': 0.9, 'correctness': 0.9, 'completeness': 0.9, 'readability': 0.9"

        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock, return_value=mock_response.content) as mock_generate_response:
            should_halt, evaluation = await quality_gate.evaluate_state(current_state, previous_state)
            assert should_halt is True
            assert evaluation['overall_quality_score'] == 0.9

    @pytest.mark.asyncio
    async def test_evaluate_state_halt_change_threshold_met(self, quality_gate, llm_manager):
        """Test evaluate_state halts when change threshold is met."""
        current_state = {'requirements': 'req', 'design': 'design', 'code': 'code'}
        previous_state = {'requirements': 'req', 'design': 'design', 'code': 'code'}
        
        mock_response = MagicMock()
        mock_response.tool_calls = None
        mock_response.content = "'overall_quality_score': 0.7, 'correctness': 0.7, 'completeness': 0.7, 'readability': 0.7"

        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock, return_value=mock_response.content) as mock_generate_response:
            should_halt, evaluation = await quality_gate.evaluate_state(current_state, previous_state)
            assert should_halt is True
            assert evaluation['change_magnitude'] == 0.0

    @pytest.mark.asyncio
    async def test_evaluate_state_continue(self, quality_gate, llm_manager):
        """Test evaluate_state continues when neither threshold is met."""
        current_state = {'requirements': 'req', 'design': 'design', 'code': 'new_code'}
        previous_state = {'requirements': 'req', 'design': 'design', 'code': 'old_code'}
        
        mock_response = MagicMock()
        mock_response.tool_calls = None
        mock_response.content = "'overall_quality_score': 0.7, 'correctness': 0.7, 'completeness': 0.7, 'readability': 0.7"

        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock, return_value=mock_response.content) as mock_generate_response:
            should_halt, evaluation = await quality_gate.evaluate_state(current_state, previous_state)
            assert should_halt is False
            assert evaluation['overall_quality_score'] == 0.7
            assert evaluation['change_magnitude'] > 0.1 # Should be greater than change_threshold

    @pytest.mark.asyncio
    async def test_evaluate_state_initial_state(self, quality_gate, llm_manager):
        """Test evaluate_state with initial state (no previous state)."""
        current_state = {'requirements': 'req', 'design': 'design', 'code': 'code'}
        previous_state = None
        
        mock_response = MagicMock()
        mock_response.tool_calls = None
        mock_response.content = "'overall_quality_score': 0.7, 'correctness': 0.7, 'completeness': 0.7, 'readability': 0.7"

        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock, return_value=mock_response.content) as mock_generate_response:
            should_halt, evaluation = await quality_gate.evaluate_state(current_state, previous_state)
            assert should_halt is False
            assert evaluation['overall_quality_score'] == 0.7
            assert evaluation['change_magnitude'] == 1.0 # Initial change magnitude should be 1.0

if __name__ == "__main__":
    pytest.main([__file__])