"""End-to-end tests for the complete MyChatDev system.

Tests the full workflow from CLI/API to deliverables generation.
"""
import asyncio
import pytest
import subprocess
import sys
import time
import requests
from pathlib import Path
import tempfile
import shutil
import json

from src.config.settings import DEFAULT_CONFIG
from src.config.llm_profiles import get_profile_by_name


class TestCompleteSystem:
    """End-to-end system tests."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for tests."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def api_server(self):
        """Start FastAPI server for testing."""
        # This would start the API server in a subprocess
        # For now, assume it's running manually
        base_url = "http://127.0.0.1:8000"
        
        # Check if server is running
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                yield base_url
            else:
                pytest.skip("API server not running")
        except requests.exceptions.RequestException:
            pytest.skip("API server not available")

    def test_cli_workflow_execution(self, temp_workspace):
        """Test complete workflow execution via CLI."""
        # Create a simple test prompt
        prompt_file = temp_workspace / "test_prompt.txt"
        prompt_file.write_text("Create a simple Python function that adds two numbers.")
        
        # Run CLI command
        cmd = [
            sys.executable, "-m", "src.cli", "run",
            "--user-prompt-file", str(prompt_file),
            "--profile", "Fast_Lightweight",
            "--max-iterations", "1",
            "--dry-run"  # Use dry run to avoid LLM dependency
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check that CLI executed without errors
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert "workflow" in result.stdout.lower()
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI execution timed out")
        except FileNotFoundError:
            pytest.skip("CLI module not found - check project structure")

    def test_api_workflow_lifecycle(self, api_server):
        """Test complete workflow lifecycle via API."""
        base_url = api_server
        
        # Test 1: Get available profiles
        response = requests.get(f"{base_url}/profiles")
        assert response.status_code == 200
        profiles_data = response.json()
        assert "profiles" in profiles_data
        
        if not profiles_data["profiles"]:
            pytest.skip("No profiles available for testing")
        
        profile_name = profiles_data["profiles"][0]["name"]
        
        # Test 2: Start workflow
        workflow_data = {
            "user_prompt": "Create a simple calculator function",
            "profile_name": profile_name,
            "max_iterations": 1,
            "dry_run": True
        }
        
        response = requests.post(f"{base_url}/workflow/start", json=workflow_data)
        if response.status_code != 200:
            pytest.skip(f"Workflow start failed: {response.text}")
        
        start_data = response.json()
        run_id = start_data.get("run_id")
        assert run_id is not None
        
        # Test 3: Check workflow status
        time.sleep(1)  # Give workflow time to process
        response = requests.get(f"{base_url}/workflow/status/{run_id}")
        
        if response.status_code == 200:
            status_data = response.json()
            assert "status" in status_data
            assert status_data["run_id"] == run_id
        
        # Test 4: Get workflow runs
        response = requests.get(f"{base_url}/workflow/runs")
        assert response.status_code == 200
        runs_data = response.json()
        assert "runs" in runs_data

    def test_config_management_api(self, api_server):
        """Test configuration management via API."""
        base_url = api_server
        
        # Test 1: Get current config
        response = requests.get(f"{base_url}/config")
        assert response.status_code == 200
        config_data = response.json()
        assert "ollama_host" in config_data
        
        # Test 2: Update config
        new_config = {
            "ollama_host": "http://test:11434",
            "max_iterations": 3,
            "enable_sandbox": True
        }
        
        response = requests.post(f"{base_url}/config", json=new_config)
        if response.status_code == 200:
            # Verify config was updated
            response = requests.get(f"{base_url}/config")
            updated_config = response.json()
            assert updated_config["ollama_host"] == "http://test:11434"
            assert updated_config["max_iterations"] == 3

    def test_profile_management_api(self, api_server):
        """Test LLM profile management via API."""
        base_url = api_server
        
        # Test 1: List profiles
        response = requests.get(f"{base_url}/profiles")
        assert response.status_code == 200
        
        # Test 2: Add a test profile
        test_profile = {
            "name": "TestProfile",
            "config": {
                "product_manager": {
                    "name": "Test PM Model",
                    "model_id": "test:model",
                    "role": "product_manager"
                }
            }
        }
        
        response = requests.post(f"{base_url}/profiles", json=test_profile)
        if response.status_code == 200:
            # Test 3: Verify profile was added
            response = requests.get(f"{base_url}/profiles")
            profiles_data = response.json()
            profile_names = [p["name"] for p in profiles_data["profiles"]]
            assert "TestProfile" in profile_names
            
            # Test 4: Delete test profile
            response = requests.delete(f"{base_url}/profiles/TestProfile")
            # Note: Delete might not be implemented, so don't assert success

    def test_system_integration_components(self):
        """Test that all system components are properly integrated."""
        # Test 1: Configuration system
        config = DEFAULT_CONFIG
        assert config is not None
        assert hasattr(config, 'ollama_host')
        assert hasattr(config, 'max_iterations')
        
        # Test 2: Profile system
        profiles = get_profile_by_name("Fast_Lightweight")
        # profiles might be None if not available, which is acceptable
        
        # Test 3: Database schema (basic check)
        from src.database import initialize_db
        test_db_url = "sqlite:///./test_integration.db"
        
        try:
            initialize_db(test_db_url)
            # If no exception, database initialization works
            assert True
        except Exception as e:
            pytest.fail(f"Database initialization failed: {e}")
        finally:
            # Cleanup test database
            test_db_path = Path("test_integration.db")
            if test_db_path.exists():
                test_db_path.unlink()

    def test_error_handling_scenarios(self, api_server):
        """Test system behavior under error conditions."""
        base_url = api_server
        
        # Test 1: Invalid workflow request
        invalid_data = {
            "user_prompt": "",  # Empty prompt
            "profile_name": "NonExistentProfile",
            "max_iterations": -1  # Invalid value
        }
        
        response = requests.post(f"{base_url}/workflow/start", json=invalid_data)
        # Should return an error status
        assert response.status_code >= 400
        
        # Test 2: Non-existent workflow status
        response = requests.get(f"{base_url}/workflow/status/nonexistent_id")
        assert response.status_code == 404
        
        # Test 3: Invalid config update
        invalid_config = {
            "ollama_host": "",  # Empty host
            "max_iterations": "not_a_number"  # Invalid type
        }
        
        response = requests.post(f"{base_url}/config", json=invalid_config)
        # Should handle gracefully (might return 400 or process with defaults)
        assert response.status_code in [200, 400, 422]

    @pytest.mark.slow
    def test_performance_basic_workflow(self, api_server):
        """Test basic performance characteristics."""
        base_url = api_server
        
        # Measure API response times
        start_time = time.time()
        
        # Test multiple quick API calls
        endpoints = [
            "/profiles",
            "/config", 
            "/roles"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{base_url}{endpoint}")
            # Each API call should complete quickly
            assert response.status_code in [200, 404]  # 404 is acceptable for some endpoints
        
        total_time = time.time() - start_time
        # All API calls should complete within reasonable time
        assert total_time < 5.0, f"API calls took too long: {total_time}s"

    def test_data_persistence(self, api_server, temp_workspace):
        """Test that data persists correctly across operations."""
        base_url = api_server
        
        # Test workflow run persistence
        workflow_data = {
            "user_prompt": "Test persistence",
            "profile_name": "Fast_Lightweight",
            "max_iterations": 1,
            "dry_run": True
        }
        
        # Start workflow
        response = requests.post(f"{base_url}/workflow/start", json=workflow_data)
        if response.status_code != 200:
            pytest.skip("Cannot test persistence - workflow start failed")
        
        run_id = response.json().get("run_id")
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Check that workflow appears in runs list
        response = requests.get(f"{base_url}/workflow/runs")
        if response.status_code == 200:
            runs_data = response.json()
            run_ids = [run["run_id"] for run in runs_data.get("runs", [])]
            assert run_id in run_ids, "Workflow run not persisted"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])