"""Unit tests for GraphWorkflow functionality.

Author: Jones Chung
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from config.settings import LLMConfig, SystemConfig, DEFAULT_CONFIG, AVAILABLE_LLMS
from models.llm_manager import LLMManager
from workflow.quality_gate import QualityGate
from workflow.sandbox import Sandbox
from workflow.graph_workflow import GraphWorkflow, GraphState
from utils.prompts import get_prompt


class TestGraphWorkflow:
    """Test cases for GraphWorkflow."""

    @pytest.fixture
    def system_config(self):
        """Sample system configuration for testing."""
        return SystemConfig(
            ollama_host="http://localhost:11434",
            max_iterations=3,
            quality_threshold=0.8,
            change_threshold=0.1,
            enable_sandbox=True,
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

    @pytest.fixture
    def sandbox(self, system_config, llm_manager, llm_configs):
        """Sandbox instance for testing."""
        return Sandbox(system_config, llm_manager, llm_configs)

    @pytest.fixture
    def graph_workflow(self, system_config, llm_manager, llm_configs, quality_gate, sandbox):
        """GraphWorkflow instance for testing."""
        with patch('workflow.graph_workflow.QualityGate', return_value=quality_gate),
             patch('workflow.graph_workflow.Sandbox', return_value=sandbox):
            return GraphWorkflow(system_config, llm_configs)

    @pytest.fixture
    def initial_state(self):
        """Initial GraphState for testing."""
        return GraphState(
            user_input="Test user input",
            requirements="",
            design="",
            code="",
            test_results="",
            review_feedback="",
            deliverables={},
            iteration_count=0,
            quality_evaluations=[],
            should_halt=False,
            strategic_guidance="",
            human_approval=False,
        )

    @pytest.mark.asyncio
    async def test_requirements_analysis_node(self, graph_workflow, initial_state, llm_manager):
        """Test requirements_analysis_node."""
        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.return_value = "Test requirements"
            result = await graph_workflow.requirements_analysis_node(initial_state)
            assert result['requirements'] == "Test requirements"

    @pytest.mark.asyncio
    async def test_system_design_node(self, graph_workflow, initial_state, llm_manager):
        """Test system_design_node."""
        state = {**initial_state, 'requirements': "Test requirements"}
        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.return_value = "Test design"
            result = await graph_workflow.system_design_node(state)
            assert result['design'] == "Test design"

    @pytest.mark.asyncio
    async def test_sandboxed_development_node(self, graph_workflow, initial_state, sandbox):
        """Test sandboxed_development_node."""
        state = {**initial_state, 'requirements': "Test requirements", 'test_results': "Test results"}
        with patch.object(sandbox, 'run_sandbox', new_callable=AsyncMock) as mock_run_sandbox:
            mock_run_sandbox.return_value = {'code_implementation': "Test code"}
            result = await graph_workflow.sandboxed_development_node(state)
            assert result['code'] == "Test code"

    @pytest.mark.asyncio
    async def test_testing_debugging_node(self, graph_workflow, initial_state, llm_manager, sandbox):
        """Test testing_debugging_node."""
        state = {**initial_state, 'code': "Test code", 'requirements': "Test requirements"}
        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock) as mock_generate_response,
             patch.object(sandbox, 'run_tests_in_sandbox', return_value="Test execution output") as mock_run_tests_in_sandbox:
            mock_generate_response.return_value = "Generated tests"
            result = await graph_workflow.testing_debugging_node(state)
            assert "Generated Tests:\nGenerated tests\n\nTest Execution Output:\nTest execution output" in result['test_results']

    @pytest.mark.asyncio
    async def test_review_refinement_node(self, graph_workflow, initial_state, llm_manager):
        """Test review_refinement_node."""
        state = {**initial_state, 'deliverables': {'code': "Test code"}}
        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.return_value = "Test review feedback"
            result = await graph_workflow.review_refinement_node(state)
            assert result['review_feedback'] == "Test review feedback"

    @pytest.mark.asyncio
    async def test_reflector_node(self, graph_workflow, initial_state, llm_manager):
        """Test reflector_node."""
        state = {**initial_state, 'quality_evaluations': [{'overall_quality_score': 0.5}]}
        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.return_value = "Test strategic guidance"
            result = await graph_workflow.reflector_node(state)
            assert result['strategic_guidance'] == "Test strategic guidance"

    @pytest.mark.asyncio
    async def test_quality_gate_node_halt(self, graph_workflow, initial_state, quality_gate):
        """Test quality_gate_node when it should halt."""
        state = {**initial_state, 'iteration_count': 2}
        with patch.object(quality_gate, 'evaluate_state', return_value=(True, {'overall_quality_score': 0.9})) as mock_evaluate_state:
            result = await graph_workflow.quality_gate_node(state)
            assert result['should_halt'] is True

    @pytest.mark.asyncio
    async def test_quality_gate_node_continue(self, graph_workflow, initial_state, quality_gate):
        """Test quality_gate_node when it should continue."""
        state = {**initial_state, 'iteration_count': 0}
        with patch.object(quality_gate, 'evaluate_state', return_value=(False, {'overall_quality_score': 0.5})) as mock_evaluate_state:
            result = await graph_workflow.quality_gate_node(state)
            assert result['should_halt'] is False
            assert result['iteration_count'] == 1

    @pytest.mark.asyncio
    async def test_output_generation_node(self, graph_workflow, initial_state):
        """Test output_generation_node."""
        result = await graph_workflow.output_generation_node(initial_state)
        assert result == {}

    def test_decide_next_step_halt(self, graph_workflow, initial_state):
        """Test decide_next_step returns 'halt' when should_halt is True."""
        state = {**initial_state, 'should_halt': True}
        result = graph_workflow.decide_next_step(state)
        assert result == "halt"

    def test_decide_next_step_reflect(self, graph_workflow, initial_state, system_config):
        """Test decide_next_step returns 'reflect' when stagnation is detected."""
        state = {**initial_state,
                 'quality_evaluations': [
                     {'overall_quality_score': 0.5, 'iteration': 0},
                     {'overall_quality_score': 0.5 + (system_config.change_threshold / 2), 'iteration': 1}
                 ]}
        result = graph_workflow.decide_next_step(state)
        assert result == "reflect"

    def test_decide_next_step_continue(self, graph_workflow, initial_state, system_config):
        """Test decide_next_step returns 'continue' when no halt or reflection is triggered."""
        state = {**initial_state,
                 'quality_evaluations': [
                     {'overall_quality_score': 0.5, 'iteration': 0},
                     {'overall_quality_score': 0.5 + (system_config.change_threshold * 2), 'iteration': 1}
                 ]}
        result = graph_workflow.decide_next_step(state)
        assert result == "continue"

if __name__ == "__main__":
    pytest.main([__file__])