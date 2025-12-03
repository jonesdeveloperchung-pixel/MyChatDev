import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock, mock_open, ANY

from src.config.settings import LLMConfig, SystemConfig, DEFAULT_CONFIG
from src.config.llm_profiles import AVAILABLE_LLMS_BY_PROFILE
from src.models.llm_manager import LLMManager
from src.workflow.quality_gate import QualityGate
from src.workflow.sandbox import Sandbox
from src.workflow.graph_workflow import GraphWorkflow, GraphState
from src.utils.prompts import get_prompt


class TestGraphWorkflowEnhancements:
    """Enhanced test cases for GraphWorkflow functionality."""

    @pytest.fixture
    def system_config(self):
        """Sample system configuration for testing."""
        return SystemConfig(
            ollama_host="http://localhost:11434",
            max_iterations=3,
            quality_threshold=0.8,
            change_threshold=0.1,
            enable_sandbox=True,
            enable_human_approval=False, # Default to false for most tests
            use_mcp_sandbox=False, # Default to false
        )

    @pytest.fixture
    def llm_configs(self):
        """Sample LLM configurations for testing."""
        return {
            "product_manager": LLMConfig(name="Mock PM", model_id="mock:pm", role="product_manager", temperature=0.5),
            "architect": LLMConfig(name="Mock Architect", model_id="mock:arch", role="architect", temperature=0.3),
            "programmer": LLMConfig(name="Mock Programmer", model_id="mock:prog", role="programmer", temperature=0.1),
            "tester": LLMConfig(name="Mock Tester", model_id="mock:tester", role="tester", temperature=0.2),
            "reviewer": LLMConfig(name="Mock Reviewer", model_id="mock:reviewer", role="reviewer", temperature=0.4),
            "reflector": LLMConfig(name="Mock Reflector", model_id="mock:reflector", role="reflector", temperature=0.6),
            "quality_gate": LLMConfig(name="Mock Quality Gate", model_id="mock:qg", role="quality_gate", temperature=0.1),
            "distiller": LLMConfig(name="Mock Distiller", model_id="mock:dist", role="distiller", temperature=0.3),
        }

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
    def sandbox(self, system_config):
        """Mock Sandbox instance for testing."""
        mock_sandbox = MagicMock(spec=Sandbox)
        mock_sandbox.config = system_config # Ensure config is available
        mock_sandbox.run_sandbox = AsyncMock(return_value={'code_implementation': "mocked code", 'tool_code': "tool.py"})
        mock_sandbox.run_tests_in_sandbox = MagicMock(return_value="mocked test output")
        return mock_sandbox

    @pytest.fixture
    def graph_workflow(self, system_config, llm_manager, llm_configs, quality_gate, sandbox):
        """GraphWorkflow instance for testing with mocked dependencies."""
        with (
            patch('src.workflow.graph_workflow.LLMManager', return_value=llm_manager),
            patch('src.workflow.graph_workflow.QualityGate', return_value=quality_gate),
            patch('src.workflow.sandbox_factory.get_sandbox_implementation', return_value=sandbox) # Corrected patch target
        ):
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
    async def test_human_approval_node_enabled(self, graph_workflow, initial_state):
        """Test human_approval_node when enabled."""
        graph_workflow.config.enable_human_approval = True
        with patch('builtins.input', return_value='approve'): # Mock user input
            result = await graph_workflow.human_approval_node(initial_state)
            assert result['human_approval'] is True

    @pytest.mark.asyncio
    async def test_human_approval_node_disabled(self, graph_workflow, initial_state):
        """Test human_approval_node when disabled (auto-approves)."""
        graph_workflow.config.enable_human_approval = False
        result = await graph_workflow.human_approval_node(initial_state)
        assert result['human_approval'] is True # Auto-approved

    def test_route_after_system_design_human_approval_enabled(self, graph_workflow, initial_state):
        """Test routing when human approval is enabled."""
        graph_workflow.config.enable_human_approval = True
        state = {**initial_state, 'requirements': "req", 'design': "design"}
        result = graph_workflow.route_after_system_design(state)
        assert result == "human_approval"

    def test_route_after_system_design_sandbox_enabled(self, graph_workflow, initial_state):
        """Test routing when sandbox is enabled and human approval is disabled."""
        graph_workflow.config.enable_human_approval = False
        graph_workflow.config.enable_sandbox = True
        state = {**initial_state, 'requirements': "req", 'design': "design"}
        result = graph_workflow.route_after_system_design(state)
        assert result == "sandboxed_development"

    def test_route_after_system_design_mcp_sandbox_enabled(self, graph_workflow, initial_state):
        """Test routing when MCP sandbox is enabled and human approval is disabled."""
        graph_workflow.config.enable_human_approval = False
        graph_workflow.config.enable_sandbox = False # Local sandbox disabled
        graph_workflow.config.use_mcp_sandbox = True # MCP sandbox enabled
        state = {**initial_state, 'requirements': "req", 'design': "design"}
        result = graph_workflow.route_after_system_design(state)
        assert result == "sandboxed_development" # Should still route to sandboxed_development

    def test_route_after_system_design_no_sandbox(self, graph_workflow, initial_state):
        """Test routing when no sandbox is enabled and human approval is disabled."""
        graph_workflow.config.enable_human_approval = False
        graph_workflow.config.enable_sandbox = False
        graph_workflow.config.use_mcp_sandbox = False
        state = {**initial_state, 'requirements': "req", 'design': "design"}
        result = graph_workflow.route_after_system_design(state)
        assert result == "code_generation_no_sandbox"

    @pytest.mark.asyncio
    async def test_code_generation_no_sandbox_node(self, graph_workflow, initial_state, llm_manager, tmp_path):
        """Test code_generation_no_sandbox_node using real temporary paths."""
        state = {**initial_state, 'requirements': "Reqs", 'design': "Design"}
        
        # Use tmp_path fixture for a real temporary directory
        graph_workflow.config.deliverables_path = tmp_path
        
        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.return_value = "Generated code without sandbox"
            
            result = await graph_workflow.code_generation_no_sandbox_node(state)
            
            assert result['code'] == "Generated code without sandbox"
            
            # Verify file was actually written to the temp path
            expected_file = tmp_path / "source_code.md"
            assert expected_file.exists()
            assert expected_file.read_text(encoding="utf-8") == "Generated code without sandbox"

    @pytest.mark.asyncio
    async def test_requirements_analysis_node_error_handling(self, graph_workflow, initial_state, llm_manager):
        """Test error handling in requirements_analysis_node."""
        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.side_effect = ValueError("Model not available")
            result = await graph_workflow.requirements_analysis_node(initial_state)
            assert "ERROR: LLM Model" in result['requirements']
            assert "ERROR: LLM Model 'mock:pm' required for Product Manager is not available. Please pull it using 'ollama pull mock:pm'." in result['requirements']

    @pytest.mark.asyncio
    async def test_full_graph_workflow_success_path(self, graph_workflow, initial_state, llm_manager, sandbox, quality_gate, system_config, tmp_path):
        """Test a full successful graph workflow run using real temporary paths."""
        
        # Use tmp_path for deliverables
        graph_workflow.config.deliverables_path = tmp_path

        def custom_side_effect(llm_config, messages):
            role = llm_config.role
            if role == "product_manager":
                return "Mocked Requirements"
            elif role == "architect":
                return "Mocked Design"
            elif role == "tester":
                return "Mocked Tests"
            elif role == "reviewer":
                return "Mocked Review Feedback"
            elif role == "reflector":
                return "Mocked Strategic Guidance"
            else:
                return "Mocked Default Response"

        with (
            patch.object(llm_manager, 'generate_response', new_callable=AsyncMock) as mock_generate_response,
            patch.object(sandbox, 'run_sandbox', new_callable=AsyncMock) as mock_run_sandbox,
            patch.object(sandbox, 'run_tests_in_sandbox', return_value="Tests passed") as mock_run_tests_in_sandbox,
            patch.object(quality_gate, 'evaluate_state', new_callable=AsyncMock) as mock_evaluate_state,
        ):
            mock_generate_response.side_effect = custom_side_effect
            
            # Mock sandbox output
            mock_run_sandbox.return_value = {'code_implementation': "Mocked Code from Sandbox"}
            
            # Mock quality gate
            mock_evaluate_state.side_effect = [
                (False, {'overall_quality_score': 0.6, 'change_magnitude': 0.2}), # Continue
                (True, {'overall_quality_score': 0.9, 'change_magnitude': 0.05}),  # Halt on second iteration
            ]

                                # Execute the graph
                                final_state = await graph_workflow.run(initial_state['user_input'])
            
                                # Assertions for the final state
                                assert final_state['requirements'] == "Mocked Requirements"
                                assert final_state['design'] == "Mocked Design"
                                assert final_state['code'] == "Mocked Code from Sandbox"
                                assert final_state['test_results'] == "Generated Tests:\nMocked Tests\n\nTest Execution Output:\nTests passed"
                                assert final_state['review_feedback'] == "Mocked Review Feedback"
                                # Strategic guidance is empty because quality gate (0.6, 0.2) did not trigger reflector
                                assert final_state['strategic_guidance'] == "" 
                                assert final_state['iteration_count'] == 2 # Started at 0, went through 2 iterations (0 and 1)
                                assert final_state['should_halt'] is True
                                assert len(final_state['quality_evaluations']) == 2
                                assert final_state['quality_evaluations'][1]['overall_quality_score'] == 0.9
                                assert final_state['deliverables']['code'] == "Mocked Code from Sandbox"            
            # Verify nodes called
            mock_run_sandbox.assert_called_once()
            mock_run_tests_in_sandbox.assert_called_once()
            assert mock_evaluate_state.call_count == 2 

            # Verify file writing to real temp path
            expected_file = tmp_path / "source_code.md"
            assert expected_file.exists()
            assert expected_file.read_text(encoding="utf-8") == "Mocked Code from Sandbox"
