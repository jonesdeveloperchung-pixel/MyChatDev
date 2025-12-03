import pytest
import httpx
import threading
import time
from datetime import datetime
from pathlib import Path
import json
import os

from src.api import app # Import the FastAPI app
from src.config.settings import SystemConfig, load_user_config, USER_CONFIG_FILE
from src.database import initialize_db, insert_workflow_run, get_db_path, update_workflow_run

# --- Fixture to run FastAPI app in a background thread ---
@pytest.fixture(scope="module")
def api_server():
    """Starts the FastAPI application in a background thread for testing."""
    # Use a specific port for testing
    port = 8002
    
    # Set a temporary database URL for testing
    test_db_dir = Path("./test_data_api_db")
    test_db_dir.mkdir(exist_ok=True)
    test_db_path = test_db_dir / "test_api.sqlite"
    test_db_url = f"sqlite:///{test_db_path}"

    # Override the database_url in a temporary SystemConfig for the API
    # This needs to be done carefully as load_user_config is a global function
    # A better approach might be to pass the system_config explicitly to the FastAPI app,
    # or use pytest-mock to mock load_user_config.
    # For now, we'll try to temporarily modify the global config and restore it.
    original_user_config = load_user_config()
    original_user_config_dict = original_user_config.model_dump()
    
    # Create a temporary config file that points to the test database
    temp_config_file_path = USER_CONFIG_FILE # This is the ~/.coopllm/config.yaml
    
    # Backup original config if it exists
    backup_config_path = None
    if temp_config_file_path.is_file():
        backup_config_path = temp_config_file_path.with_suffix(".yaml.bak")
        temp_config_file_path.rename(backup_config_path)

    # Create a new config file for testing
    test_config_data = original_user_config_dict.copy()
    test_config_data['database_url'] = test_db_url
    
    # Convert Path objects to strings for JSON serialization
    for key, value in test_config_data.items():
        if isinstance(value, Path):
            test_config_data[key] = str(value)

    with open(temp_config_file_path, 'w', encoding='utf-8') as f:
        json.dump(test_config_data, f, indent=2)

    # Initialize the database for testing
    initialize_db(test_db_url)

    # Use a function to run uvicorn to be targetable by thread
    def run_api():
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="critical") # Use critical log level to suppress output

    server_thread = threading.Thread(target=run_api, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give the server a moment to start up

    yield f"http://127.0.0.1:{port}"

    # Clean up after tests
    # Restore original config file or delete temporary one
    if temp_config_file_path.is_file():
        temp_config_file_path.unlink()
    if backup_config_path and backup_config_path.is_file():
        backup_config_path.rename(temp_config_file_path)

    # Clean up the test database file and directory after tests
    if test_db_path.exists():
        test_db_path.unlink()
    if test_db_dir.exists():
        test_db_dir.rmdir()


# --- Fixture to populate test data ---
@pytest.fixture(scope="module")
def populate_db_with_workflow_runs(api_server): # Depend on api_server to ensure it's running
    """Populates the test database with some workflow run data."""
    current_config = load_user_config() # Get config with the test_db_url from the fixture
    db_url = current_config.database_url

    # Insert a completed run
    insert_workflow_run(
        run_id="test_run_completed",
        status="completed",
        start_time=datetime(2023, 1, 1, 10, 0, 0).isoformat(),
        user_prompt="Implement a feature that calculates Fibonacci numbers.",
        config_used=SystemConfig(max_iterations=5).model_dump_json(),
        database_url=db_url
    )
    update_workflow_run(
        run_id="test_run_completed",
        end_time=datetime(2023, 1, 1, 10, 5, 0).isoformat(),
        review_feedback="Code is correct and well-documented.",
        deliverables_path="./deliverables/test_run_completed",
        database_url=db_url
    )

    # Insert a running run
    insert_workflow_run(
        run_id="test_run_running",
        status="running",
        start_time=datetime(2023, 1, 2, 11, 0, 0).isoformat(),
        user_prompt="Develop a simple web server.",
        config_used=SystemConfig(max_iterations=10).model_dump_json(),
        database_url=db_url
    )

    # Insert an error run
    insert_workflow_run(
        run_id="test_run_error",
        status="error",
        start_time=datetime(2023, 1, 3, 12, 0, 0).isoformat(),
        user_prompt="Create a login form with validation.",
        config_used=SystemConfig(max_iterations=3).model_dump_json(),
        database_url=db_url
    )
    update_workflow_run(
        run_id="test_run_error",
        end_time=datetime(2023, 1, 3, 12, 2, 0).isoformat(),
        review_feedback="Workflow terminated with error: LLM model not found.",
        deliverables_path="./deliverables/test_run_error",
        database_url=db_url
    )

    yield # Let tests run


class TestAPIDatabaseEndpoints:

    def test_get_workflow_status_existing(self, api_server, populate_db_with_workflow_runs):
        """Test retrieving status for an existing workflow run from the database."""
        with httpx.Client(base_url=api_server) as client:
            response = client.get("/workflow/status/test_run_completed")
            assert response.status_code == 200
            data = response.json()
            assert data["run_id"] == "test_run_completed"
            assert data["status"] == "completed"
            assert "config_used" in data
            assert isinstance(data["config_used"], dict) # Should be parsed JSON
            assert data["review_feedback"] == "Code is correct and well-documented."
            assert data["deliverables_path"] == "./deliverables/test_run_completed"

    def test_get_workflow_status_not_found(self, api_server):
        """Test retrieving status for a non-existent workflow run."""
        with httpx.Client(base_url=api_server) as client:
            response = client.get("/workflow/status/non_existent_run")
            assert response.status_code == 404
            assert "not found in database" in response.json()["detail"]

    def test_get_all_workflow_runs(self, api_server, populate_db_with_workflow_runs):
        """Test retrieving all workflow runs from the database."""
        with httpx.Client(base_url=api_server) as client:
            response = client.get("/workflow/runs")
            assert response.status_code == 200
            data = response.json()
            assert "runs" in data
            assert len(data["runs"]) == 3

            # Check some data from the runs
            run_ids = {run["run_id"] for run in data["runs"]}
            assert "test_run_completed" in run_ids
            assert "test_run_running" in run_ids
            assert "test_run_error" in run_ids

            # Verify sorting (newest first based on start_time in fixture)
            assert data["runs"][0]["run_id"] == "test_run_error" # This order depends on the insertion order and start_time
            assert data["runs"][1]["run_id"] == "test_run_running"
            assert data["runs"][2]["run_id"] == "test_run_completed"

            # Check a specific field
            completed_run = next(run for run in data["runs"] if run["run_id"] == "test_run_completed")
            assert completed_run["status"] == "completed"
            assert completed_run["review_feedback"] == "Code is correct and well-documented."

            error_run = next(run for run in data["runs"] if run["run_id"] == "test_run_error")
            assert error_run["status"] == "error"
            assert error_run["user_prompt"] == "Create a login form with validation."
