import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
import json

from src.database import get_connection, initialize_db, insert_workflow_run, update_workflow_run, get_workflow_run, get_all_workflow_runs
from src.config.settings import SystemConfig, LLMConfig

# Use a temporary database file for testing
TEST_DB_URL = "sqlite:///./test_data/test_db.sqlite"

@pytest.fixture(autouse=True)
def setup_teardown_db():
    """Fixture to set up and tear down the database for each test."""
    db_path = Path(TEST_DB_URL.replace("sqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure a clean slate before each test
    if db_path.exists():
        db_path.unlink()

    initialize_db(TEST_DB_URL)
    yield
    # Clean up after each test
    if db_path.exists():
        db_path.unlink()
    if db_path.parent.exists():
        db_path.parent.rmdir()


def test_get_connection():
    """Test that a database connection can be established."""
    conn = get_connection(TEST_DB_URL)
    assert isinstance(conn, sqlite3.Connection)
    conn.close()

def test_initialize_db():
    """Test that the workflow_runs table is created."""
    conn = get_connection(TEST_DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_runs';")
    assert cursor.fetchone() is not None
    conn.close()

def test_insert_workflow_run():
    """Test inserting a new workflow run."""
    run_id = "test_run_123"
    status = "running"
    start_time = datetime.now().isoformat()
    user_prompt = "Develop a simple calculator"
    config_used = SystemConfig().model_dump_json()

    inserted_id = insert_workflow_run(run_id, status, start_time, user_prompt, config_used, TEST_DB_URL)
    assert inserted_id is not None

    conn = get_connection(TEST_DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workflow_runs WHERE run_id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row['run_id'] == run_id
    assert row['status'] == status
    assert row['user_prompt'] == user_prompt
    assert json.loads(row['config_used']) == json.loads(config_used) # Compare JSON content

def test_get_workflow_run():
    """Test retrieving a single workflow run by ID."""
    run_id = "test_run_get"
    status = "running"
    start_time = datetime.now().isoformat()
    user_prompt = "Test retrieval"
    config_used = SystemConfig().model_dump_json()
    insert_workflow_run(run_id, status, start_time, user_prompt, config_used, TEST_DB_URL)

    retrieved_run = get_workflow_run(run_id, TEST_DB_URL)
    assert retrieved_run is not None
    assert retrieved_run['run_id'] == run_id
    assert retrieved_run['status'] == status

    # Test non-existent run
    assert get_workflow_run("non_existent_run", TEST_DB_URL) is None

def test_update_workflow_run():
    """Test updating an existing workflow run."""
    run_id = "test_run_update"
    status = "running"
    start_time = datetime.now().isoformat()
    user_prompt = "Test update"
    config_used = SystemConfig().model_dump_json()
    insert_workflow_run(run_id, status, start_time, user_prompt, config_used, TEST_DB_URL)

    new_status = "completed"
    end_time = datetime.now().isoformat()
    review_feedback = "Good job"
    deliverables_path = "/path/to/deliverables"

    update_workflow_run(
        run_id,
        status=new_status,
        end_time=end_time,
        review_feedback=review_feedback,
        deliverables_path=deliverables_path,
        database_url=TEST_DB_URL
    )

    updated_run = get_workflow_run(run_id, TEST_DB_URL)
    assert updated_run is not None
    assert updated_run['status'] == new_status
    assert updated_run['end_time'] == end_time
    assert updated_run['review_feedback'] == review_feedback
    assert updated_run['deliverables_path'] == deliverables_path

def test_get_all_workflow_runs():
    """Test retrieving all workflow runs."""
    insert_workflow_run("run_a", "running", datetime.now().isoformat(), "Prompt A", "{}", TEST_DB_URL)
    insert_workflow_run("run_b", "completed", datetime.now().isoformat(), "Prompt B", "{}", TEST_DB_URL)

    all_runs = get_all_workflow_runs(TEST_DB_URL)
    assert len(all_runs) == 2
    # Ensure they are sorted by start_time DESC (newest first based on current insertion)
    assert all_runs[0]['run_id'] == "run_b"
    assert all_runs[1]['run_id'] == "run_a"
