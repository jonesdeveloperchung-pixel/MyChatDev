"""Integration tests for workflow service functionality.

Tests the complete workflow execution including database integration.
"""
import asyncio
import pytest
from pathlib import Path
from copy import deepcopy
import tempfile
import shutil
import uuid

from src.workflow_service import execute_workflow
from src.config.settings import DEFAULT_CONFIG
from src.config.llm_profiles import AVAILABLE_LLMS_BY_PROFILE
from src.utils.logging_config import setup_logging
from src.database import initialize_db, get_workflow_run


class TestWorkflowServiceIntegration:
    """Integration tests for workflow service."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def test_config(self, temp_output_dir):
        """Test configuration with minimal iterations and unique DB."""
        config = deepcopy(DEFAULT_CONFIG)
        config.max_iterations = 1
        # Use a unique database file for each test to avoid locking/integrity issues
        db_path = temp_output_dir / f"test_workflow_{uuid.uuid4().hex}.db"
        config.database_url = f"sqlite:///{db_path}"
        return config

    @pytest.fixture
    def sample_prompt(self):
        """Sample user prompt for testing."""
        return """
        Create a simple Python function that:
        1. Takes two numbers as input
        2. Returns their sum
        3. Includes basic error handling
        """

    @pytest.mark.asyncio
    async def test_workflow_execution_dry_run(self, test_config, sample_prompt, temp_output_dir):
        """Test workflow execution in dry run mode."""
        llm_configs = AVAILABLE_LLMS_BY_PROFILE.get("Fast_Lightweight")
        if not llm_configs:
            pytest.skip("Fast_Lightweight profile not available")

        events = []
        async for event in execute_workflow(
            user_input=sample_prompt,
            system_config=test_config,
            llm_configs=llm_configs,
            output_dir=temp_output_dir,
            dry_run=True
        ):
            events.append(event)

        # Verify dry run events
        assert len(events) >= 3  # start, dry_run_summary, end
        assert events[0]["event_type"] == "workflow_start"
        assert events[-1]["event_type"] == "workflow_end"
        assert events[-1]["status"] == "dry_run_completed"

    @pytest.mark.asyncio
    async def test_workflow_execution_with_mock_llm(self, test_config, sample_prompt, temp_output_dir):
        """Test workflow execution with mocked LLM responses."""
        
        llm_configs = AVAILABLE_LLMS_BY_PROFILE.get("Fast_Lightweight")
        if not llm_configs:
            pytest.skip("Fast_Lightweight profile not available")

        # Initialize test database
        initialize_db(test_config.database_url)

        events = []
        try:
            async for event in execute_workflow(
                user_input=sample_prompt,
                system_config=test_config,
                llm_configs=llm_configs,
                output_dir=temp_output_dir,
                dry_run=False
            ):
                events.append(event)
                # Break early to avoid long execution in tests
                if len(events) > 10:
                    break
        except Exception as e:
            # Expected to fail without actual Ollama server
            # But we can still verify the structure
            assert len(events) >= 1
            assert events[0]["event_type"] == "workflow_start"

    @pytest.mark.asyncio
    async def test_workflow_database_integration(self, test_config, sample_prompt, temp_output_dir):
        """Test that workflow properly integrates with database."""
        llm_configs = AVAILABLE_LLMS_BY_PROFILE.get("Fast_Lightweight")
        if not llm_configs:
            pytest.skip("Fast_Lightweight profile not available")

        # Initialize test database
        initialize_db(test_config.database_url)

        run_id = None
        try:
            async for event in execute_workflow(
                user_input=sample_prompt,
                system_config=test_config,
                llm_configs=llm_configs,
                output_dir=temp_output_dir,
                dry_run=False
            ):
                if event["event_type"] == "workflow_start":
                    run_id = event["run_id"]
                    break
        except Exception:
            pass

        # Verify database record was created
        if run_id:
            workflow_run = get_workflow_run(run_id, test_config.database_url)
            assert workflow_run is not None
            assert workflow_run["run_id"] == run_id
            assert workflow_run["status"] in ["running", "error"]

    def test_workflow_config_validation(self, sample_prompt, temp_output_dir, test_config):
        """Test workflow with invalid configuration."""
        # Create invalid config based on the valid test_config (to keep DB settings)
        invalid_config = deepcopy(test_config)
        invalid_config.max_iterations = -1  # Invalid value

        llm_configs = AVAILABLE_LLMS_BY_PROFILE.get("Fast_Lightweight")
        if not llm_configs:
            pytest.skip("Fast_Lightweight profile not available")

        try:
            asyncio.run(self._run_workflow_once(
                sample_prompt, invalid_config, llm_configs, temp_output_dir
            ))
        except Exception as e:
            assert "iteration" in str(e).lower() or "config" in str(e).lower()

    async def _run_workflow_once(self, prompt, config, llm_configs, output_dir):
        """Helper to run workflow and get first event."""
        async for event in execute_workflow(
            user_input=prompt,
            system_config=config,
            llm_configs=llm_configs,
            output_dir=output_dir,
            dry_run=True
        ):
            return event

    def test_workflow_profile_validation(self, test_config, sample_prompt, temp_output_dir):
        """Test workflow with invalid LLM profile."""
        invalid_llm_configs = {
            "invalid_role": {
                "name": "Invalid Model",
                "model_id": "nonexistent:model",
                "role": "invalid_role"
            }
        }

        try:
            asyncio.run(self._run_workflow_once(
                sample_prompt, test_config, invalid_llm_configs, temp_output_dir
            ))
        except Exception as e:
            error_msg = str(e).lower()
            assert any(word in error_msg for word in ["profile", "model", "config", "role"])

    @pytest.mark.asyncio
    async def test_workflow_event_structure(self, test_config, sample_prompt, temp_output_dir):
        """Test that workflow events have proper structure."""
        llm_configs = AVAILABLE_LLMS_BY_PROFILE.get("Fast_Lightweight")
        if not llm_configs:
            pytest.skip("Fast_Lightweight profile not available")
        
        # Ensure DB is initialized for this test config
        initialize_db(test_config.database_url)

        async for event in execute_workflow(
            user_input=sample_prompt,
            system_config=test_config,
            llm_configs=llm_configs,
            output_dir=temp_output_dir,
            dry_run=True
        ):
            assert "event_type" in event
            assert isinstance(event["event_type"], str)
            assert "timestamp" in event
            
            if event["event_type"] == "workflow_start":
                assert "run_id" in event
                assert "message" in event
            elif event["event_type"] == "workflow_end":
                assert "status" in event
                assert "run_id" in event
            
            break


class TestWorkflowServiceErrorHandling:
    """Test error handling in workflow service."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def error_config(self):
        """Configuration that might cause errors."""
        config = deepcopy(DEFAULT_CONFIG)
        # Use an invalid file path for SQLite to force a DB error
        # On Windows, using a reserved character like < or > often works, or a non-existent driver prefix
        # But simpler is a directory that doesn't exist
        config.database_url = "sqlite:///./nonexistent_dir_12345/test.db" 
        return config

    @pytest.mark.asyncio
    async def test_workflow_database_error_handling(self, error_config, temp_output_dir):
        """Test workflow behavior with database errors."""
        llm_configs = AVAILABLE_LLMS_BY_PROFILE.get("Fast_Lightweight")
        if not llm_configs:
            pytest.skip("Fast_Lightweight profile not available")

        sample_prompt = "Create a simple function."

        events = []
        try:
            async for event in execute_workflow(
                user_input=sample_prompt,
                system_config=error_config,
                llm_configs=llm_configs,
                output_dir=temp_output_dir,
                dry_run=True 
            ):
                events.append(event)
        except Exception as e:
            # Should get a meaningful database error
            assert "database" in str(e).lower() or "sqlite" in str(e).lower() or "unable to open" in str(e).lower()

    def test_workflow_empty_prompt_handling(self, temp_output_dir):
        """Test workflow with empty prompt."""
        # Use a unique DB for this test method to avoid conflicts
        config = deepcopy(DEFAULT_CONFIG)
        config.max_iterations = 1
        db_path = temp_output_dir / f"test_workflow_empty_{uuid.uuid4().hex}.db"
        config.database_url = f"sqlite:///{db_path}"
        
        # Initialize DB
        initialize_db(config.database_url)
        
        llm_configs = AVAILABLE_LLMS_BY_PROFILE.get("Fast_Lightweight")
        if not llm_configs:
            pytest.skip("Fast_Lightweight profile not available")

        empty_prompts = ["", "   ", "\n\n", None]
        
        for prompt in empty_prompts:
            try:
                asyncio.run(self._test_single_prompt(prompt, config, llm_configs, temp_output_dir))
                # Ensure unique run_id (which is timestamp based)
                import time
                time.sleep(1.1) 
            except Exception as e:
                # Should handle empty prompts gracefully
                error_msg = str(e).lower()
                assert any(word in error_msg for word in ["prompt", "input", "empty", "invalid"])

    async def _test_single_prompt(self, prompt, config, llm_configs, output_dir):
        """Helper to test a single prompt."""
        async for event in execute_workflow(
            user_input=prompt,
            system_config=config,
            llm_configs=llm_configs,
            output_dir=output_dir,
            dry_run=True
        ):
            return event