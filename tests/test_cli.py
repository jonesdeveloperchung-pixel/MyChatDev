import pytest
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os
import shutil
import time # Added for sleep

# Adjust path to import cli.py
# Import CLI symbols used by these tests so names like DEFAULT_CONFIG are defined.
from cli import cli_main, DEFAULT_CONFIG, USER_PROFILES_DIR, USER_CONFIG_FILE

@pytest.fixture
def tmp_dirs(tmp_path):
    """
    Provides a temporary directory for tests and ensures a cleaned up
    .coopllm directory is available under the temporary path.
    """
    temp_coopllm_dir = tmp_path / ".coopllm"
    temp_coopllm_dir.mkdir(parents=True, exist_ok=True)
    # Create typical subdirectories used by tests
    (temp_coopllm_dir / "profiles").mkdir(parents=True, exist_ok=True)
    try:
        yield tmp_path
    finally:
        # Explicitly clean up the temporary .coopllm directory
        time.sleep(0.1) # Add a small delay to release file handles
        if temp_coopllm_dir.exists():
            shutil.rmtree(temp_coopllm_dir)

# Helper to run cli_main with custom arguments and capture output
@pytest.mark.asyncio
async def run_cli_and_capture_output(args):
    with (
        patch('sys.stdout', new_callable=MagicMock) as mock_stdout,
        patch('sys.stderr', new_callable=MagicMock) as mock_stderr,
        patch('sys.exit') as mock_exit
    ):
        mock_exit.side_effect = SystemExit # Ensure sys.exit raises an exception
        try:
            await cli_main(argv=args)
        except SystemExit as e:
            # Capture the exit code if sys.exit was called
            pass # We expect SystemExit for validation failures
        finally:
            stdout_output = mock_stdout.getvalue()
            stderr_output = mock_stderr.getvalue()
            exit_code = mock_exit.call_args[0][0] if mock_exit.called else 0
            return stdout_output, stderr_output, exit_code


# --- Test Cases for 'run' command ---
@pytest.mark.asyncio
async def test_run_command_default_settings(tmp_dirs):
    # Mock the GraphWorkflow to prevent actual LLM calls during testing
    with (
        patch('cli.GraphWorkflow') as MockGraphWorkflow,
        patch('cli.save_deliverables', return_value=(Path("mock_deliverables"), "timestamp")),
        patch('builtins.print') as mock_print
    ):
        
        MockGraphWorkflow.return_value.run.return_value = {
            "user_input": "test",
            "deliverables": {},
            "quality_evaluations": [],
            "iteration_count": 1
        } # Mock return value

        stdout, stderr, exit_code = await run_cli_and_capture_output(["run"])
        assert exit_code == 0
        assert "COOPERATIVE LLM SYSTEM STARTUP" in stdout
        assert "No user prompt provided. Using default built-in prompt." in stdout
        assert "No profile specified. Using default built-in profile." in stdout
        MockGraphWorkflow.assert_called_once() # Ensure workflow was attempted
default_profile = DEFAULT_CONFIG.copy()

async def test_run_command_demo_mode(tmp_dirs):
    # Mock the GraphWorkflow to prevent actual LLM calls during testing
    with (
        patch('cli.GraphWorkflow') as MockGraphWorkflow,
        patch('cli.save_deliverables', return_value=(Path("mock_deliverables_demo"), "timestamp_demo")),
        patch('builtins.print') as mock_print
    ):

        MockGraphWorkflow.return_value.run.return_value = {
            "user_input": "demo test",
            "deliverables": {},
            "quality_evaluations": [],
            "iteration_count": 1
        } # Mock return value

        stdout, stderr, exit_code = await run_cli_and_capture_output(["run", "--demo"])
        assert exit_code == 0
        assert "Running in demo mode. Overriding some settings." in stdout
        assert MockGraphWorkflow.called # Ensure workflow was attempted

@pytest.mark.asyncio
async def test_run_command_dry_run_mode(tmp_dirs):
    # Mock GraphWorkflow and save_deliverables to ensure they are NOT called
    with (
        patch('cli.GraphWorkflow') as MockGraphWorkflow,
        patch('cli.save_deliverables') as MockSaveDeliverables,
        patch('builtins.print') as mock_print
    ):
        
        stdout, stderr, exit_code = await run_cli_and_capture_output(["run", "--dry-run"])
        assert exit_code == 0
        assert "Dry run enabled. Skipping actual workflow execution and deliverable saving." in stdout
        assert "Dry Run Summary" in stdout
        MockGraphWorkflow.assert_not_called()
        MockSaveDeliverables.assert_not_called()

@pytest.mark.asyncio
async def test_run_command_output_dir(tmp_dirs):
    test_output_dir = tmp_dirs / "custom_output"
    with (
        patch('cli.GraphWorkflow') as MockGraphWorkflow,
        patch('cli.save_deliverables') as MockSaveDeliverables,
        patch('builtins.print') as mock_print
    ):
        
        MockGraphWorkflow.return_value.run.return_value = {
            "user_input": "test",
            "deliverables": {},
            "quality_evaluations": [],
            "iteration_count": 1
        } # Mock return value
        
        # Mock save_deliverables to inspect passed output_dir
        MockSaveDeliverables.return_value=(test_output_dir / "timestamp", "timestamp")

        stdout, stderr, exit_code = await run_cli_and_capture_output(["run", "--output-dir", str(test_output_dir)])
        assert exit_code == 0
        assert MockSaveDeliverables.called
        # Check if save_deliverables was called with the correct output_dir
        call_args, _ = MockSaveDeliverables.call_args
        assert call_args[1] == test_output_dir

# --- Test Cases for 'profile' command ---
@pytest.mark.asyncio
async def test_profile_list_command(tmp_dirs):
    stdout, stderr, exit_code = await run_cli_and_capture_output(["profile", "list"])
    assert exit_code == 0
    assert "Available LLM Profiles" in stdout
    assert "High_Reasoning (Built-in)" in stdout

@pytest.mark.asyncio
async def test_profile_show_command(tmp_dirs):
    stdout, stderr, exit_code = await run_cli_and_capture_output(["profile", "show", "High_Reasoning"])
    assert exit_code == 0
    assert "Details for Profile 'High_Reasoning'" in stdout
    assert "Product Manager: gemma3:12b (temp=0.4)" in stdout # Check a specific detail

@pytest.mark.asyncio
async def test_profile_add_and_show_custom_profile(tmp_dirs):
    custom_profile_content = """
product_manager:
  model_id: custom-pm:latest
  temperature: 0.5
architect:
  model_id: custom-arch:latest
  temperature: 0.3
"""
    custom_profile_file = tmp_dirs / "custom_profile.yaml"
    custom_profile_file.write_text(custom_profile_content)

    # Add the profile
    stdout, stderr, exit_code = await run_cli_and_capture_output(["profile", "add", "my_custom", str(custom_profile_file)])
    assert exit_code == 0
    assert "Profile 'my_custom' added successfully" in stdout
    assert (USER_PROFILES_DIR / "my_custom.yaml").is_file()

    # Show the custom profile
    stdout, stderr, exit_code = await run_cli_and_capture_output(["profile", "show", "my_custom"])
    assert exit_code == 0
    assert "Details for Profile 'my_custom'" in stdout
    assert "Product Manager: custom-pm:latest (temp=0.5)" in stdout

@pytest.mark.asyncio
async def test_profile_delete_custom_profile(tmp_dirs):
    # First, add a profile to delete
    custom_profile_content = """
product_manager:
  model_id: to-delete:latest
  temperature: 0.5
"""
    custom_profile_file = (tmp_dirs / ".coopllm" / "profiles") / "delete_me.yaml"
    custom_profile_file.parent.mkdir(exist_ok=True)
    custom_profile_file.write_text(custom_profile_content)
    assert custom_profile_file.is_file()

    stdout, stderr, exit_code = await run_cli_and_capture_output(["profile", "delete", "delete_me"])
    assert exit_code == 0
    assert "Profile 'delete_me' deleted successfully." in stdout
    assert not custom_profile_file.is_file()

# --- Test Cases for 'config' command ---
@pytest.mark.asyncio
async def test_config_show_command(tmp_dirs):
    stdout, stderr, exit_code = await run_cli_and_capture_output(["config", "show"])
    assert exit_code == 0
    assert "Current System Configuration" in stdout
    assert f"  ollama_host: http://localhost:11434" in stdout # Default should be present

@pytest.mark.asyncio
async def test_config_set_and_show_command(tmp_dirs):
    stdout, stderr, exit_code = await run_cli_and_capture_output(["config", "set", "max_iterations", "5"])
    assert exit_code == 0
    assert "Configuration updated: max_iterations = 5" in stdout

    stdout, stderr, exit_code = await run_cli_and_capture_output(["config", "show"])
    assert exit_code == 0
    assert "  max_iterations: 5" in stdout

@pytest.mark.asyncio
async def test_config_set_invalid_key(tmp_dirs):
    stdout, stderr, exit_code = await run_cli_and_capture_output(["config", "set", "non_existent_key", "value"])
    assert exit_code == SystemExit # Expected to exit with an error
    assert "Error: Unknown configuration key: 'non_existent_key'." in stderr

@pytest.mark.asyncio
async def test_config_reset_command(tmp_dirs):
    # First, set a custom config to ensure reset has something to do
    await run_cli_and_capture_output(["config", "set", "max_iterations", "99"])
    assert USER_CONFIG_FILE.is_file()

    stdout, stderr, exit_code = await run_cli_and_capture_output(["config", "reset"])
    assert exit_code == 0
    assert "User configuration file" in stdout and "deleted" in stdout
    assert not USER_CONFIG_FILE.is_file()

@pytest.mark.asyncio
async def test_config_edit_command(tmp_dirs):
    with patch('os.system') as mock_os_system:
        stdout, stderr, exit_code = await run_cli_and_capture_output(["config", "edit"])
        assert exit_code == 0
        mock_os_system.assert_called_once() # Verify editor was attempted to be opened
        assert str(USER_CONFIG_FILE) in mock_os_system.call_args[0][0]

# --- Test Cases for 'debug' command ---
@pytest.mark.asyncio
async def test_debug_log_command(tmp_path: Path, tmp_dirs):
    # Create a dummy debug.log file
    dummy_log_content = "DEBUG: Test log entry\nINFO: Another entry"
    (tmp_path / "debug.log").write_text(dummy_log_content)

    # Patch Path("debug.log") to point to our dummy file
    with patch('cli.Path', wraps=Path) as MockPath:
        MockPath.return_value = tmp_path / "debug.log"
        stdout, stderr, exit_code = await run_cli_and_capture_output(["debug", "log"])
        assert exit_code == 0
        assert dummy_log_content in stdout
        assert "--- Content of debug.log ---" in stdout

@pytest.mark.asyncio
async def test_debug_log_command_no_file(tmp_dirs):
    stdout, stderr, exit_code = await run_cli_and_capture_output(["debug", "log"])
    assert exit_code == 0
    assert "No debug log file found" in stdout

# --- Test Cases for 'info' command ---
@pytest.mark.asyncio
async def test_info_version_command(tmp_dirs):
    stdout, stderr, exit_code = await run_cli_and_capture_output(["info", "version"])
    assert exit_code == 0
    assert "Cooperative LLM CLI Version: 0.1.0" in stdout

@pytest.mark.asyncio
async def test_info_system_command(tmp_dirs):
    stdout, stderr, exit_code = await run_cli_and_capture_output(["info", "system"])
    assert exit_code == 0
    assert "--- System Information ---" in stdout
    assert "Operating System:" in stdout
    assert "Python Version:" in stdout
    assert "Current Working Directory:" in stdout
    assert "User home:" in stdout

# --- Test Cases for invalid commands / help ---
@pytest.mark.asyncio
async def test_cli_main_no_command():
    stdout, stderr, exit_code = await run_cli_and_capture_output([])
    assert exit_code == 1 # Expecting an error exit code
    assert "Available commands" in stdout # Should print help text

@pytest.mark.asyncio
async def test_cli_main_unknown_command():
    stdout, stderr, exit_code = await run_cli_and_capture_output(["unknown_cmd"])
    assert exit_code == 2 # argparse exits with 2 for unknown args
    assert "invalid choice: 'unknown_cmd'" in stderr

@pytest.mark.asyncio
async def test_run_command_help():
    stdout, stderr, exit_code = await run_cli_and_capture_output(["run", "--help"])
    assert exit_code == 0
    assert "Execute the cooperative LLM workflow" in stdout
    assert "Input Options" in stdout
    assert "Examples:" in stdout

@pytest.mark.asyncio
async def test_profile_add_command_invalid_file(tmp_dirs):
    stdout, stderr, exit_code = await run_cli_and_capture_output(["profile", "add", "bad_profile", str(tmp_dirs / "non_existent.yaml")])
