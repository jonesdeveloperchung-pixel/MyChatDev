import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import os
import shutil

from workflow.sandbox import Sandbox
from config.settings import SystemConfig, LLMConfig # Import LLMConfig
from models.llm_manager import LLMManager # Import LLMManager

@pytest.fixture
def mock_system_config(tmp_path):
    """Provides a mock SystemConfig instance for testing."""
    mock = MagicMock(spec=SystemConfig)
    mock.deliverables_path = tmp_path / "mock_deliverables"
    mock.deliverables_path.mkdir(exist_ok=True)
    mock.enable_sandbox = True # Ensure sandbox is enabled for tests
    return mock

# Fixture for a temporary sandbox directory
@pytest.fixture
def temp_sandbox_dir(tmp_path):
    """
    Provides a temporary directory for sandbox operations.
    `tmp_path` is a pytest fixture that provides a unique temporary directory.
    """
    sandbox_path = tmp_path / "test_sandbox"
    sandbox_path.mkdir()
    yield sandbox_path
    # Cleanup is handled by tmp_path fixture automatically (via finalizer of tmp_path)

@pytest.fixture
def mock_llm_manager():
    """Provides a mock LLMManager instance for testing."""
    mock = MagicMock(spec=LLMManager)
    # Configure specific mock behaviors if needed
    mock.compress_content.return_value = "compressed content"
    return mock

@pytest.fixture
def mock_llm_configs():
    """Provides mock LLM configurations for testing."""
    return {
        "distiller": LLMConfig(name="Mock Distiller", model_id="mock:distiller", role="distiller", temperature=0.3)
    }

@pytest.fixture
def sandbox_instance(mock_system_config, mock_llm_manager, mock_llm_configs):
    """
    Provides a Sandbox instance initialized with a temporary directory
    and mock LLMManager and LLM configs.
    """
    sandbox = Sandbox(mock_system_config, mock_llm_manager, mock_llm_configs)
    yield sandbox
    # No explicit cleanup needed here as temp_sandbox_dir handles it.

class TestSandbox:
    """
    Test cases for the Sandbox class.
    """

    def test_sandbox_initialization(self, mock_system_config, mock_llm_manager, mock_llm_configs):
        """
        Tests that the Sandbox initializes correctly and creates its directory.
        """
        sandbox = Sandbox(mock_system_config, mock_llm_manager, mock_llm_configs)
        assert sandbox.config == mock_system_config
        assert sandbox.sandbox_dir == os.path.join(mock_system_config.deliverables_path, "sandbox")
        assert Path(sandbox.sandbox_dir).is_dir()

    async def test_write_file_success(self, sandbox_instance):
        """
        Tests successful writing of a file within the sandbox.
        """
        abs_path = sandbox_instance._write_file(file_path, content) # Changed to _write_file

        expected_abs_path = Path(sandbox_instance.sandbox_dir) / file_path # Changed sandbox_path to sandbox_dir
        assert abs_path == str(expected_abs_path)
        assert expected_abs_path.is_file()
        assert expected_abs_path.read_text() == content

    async def test_write_file_subdirectory(self, sandbox_instance):
        """
        Tests writing a file in a subdirectory within the sandbox.
        """
        file_path = "subdir/nested_file.txt"
        content = "Nested content."
        abs_path = sandbox_instance._write_file(file_path, content) # Changed to _write_file

        expected_abs_path = Path(sandbox_instance.sandbox_dir) / file_path # Changed sandbox_path to sandbox_dir
        assert abs_path == str(expected_abs_path)
        assert expected_abs_path.is_file()
        assert expected_abs_path.read_text() == content
        assert (Path(sandbox_instance.sandbox_dir) / "subdir").is_dir()

    async def test_read_file_success(self, sandbox_instance):
        """
        Tests successful reading of a file within the sandbox.
        """
        file_path = "read_me.txt"
        content = "Content to be read."
        (Path(sandbox_instance.sandbox_dir) / file_path).write_text(content) # Changed sandbox_path to sandbox_dir

        read_content = sandbox_instance._read_file(file_path) # Changed to _read_file
        assert read_content == content

    async def test_read_file_non_existent(self, sandbox_instance):
        """
        Tests reading a non-existent file within the sandbox.
        """
        with pytest.raises(FileNotFoundError):
            sandbox_instance._read_file("non_existent.txt") # Changed to _read_file

    async def test_run_shell_command_success(self, sandbox_instance):
        """
        Tests successful execution of a simple shell command.
        """
        command = "echo Hello from shell"
        result = sandbox_instance._run_shell_command(command) # Changed to _run_shell_command

        assert result["stdout"].strip() == "Hello from shell"
        assert result["stderr"] == ""
        assert result["exit_code"] == 0

    async def test_run_shell_command_error(self, sandbox_instance):
        """
        Tests execution of a shell command that produces an error.
        """
        command = "exit 1" # A command that explicitly exits with an error code
        result = sandbox_instance._run_shell_command(command) # Changed to _run_shell_command

        assert result["stdout"] == ""
        assert result["stderr"] == "" # On Windows, 'exit 1' doesn't write to stderr
        assert result["exit_code"] == 1

    async def test_run_shell_command_timeout(self, sandbox_instance):
        """
        Tests a shell command that exceeds the timeout.
        """
        # Use a command that sleeps for longer than the timeout
        command = "timeout 5" if os.name == "nt" else "sleep 5" # Windows 'timeout' command, Unix 'sleep'
        
        # Patch the actual subprocess.run to simulate a timeout
        with patch('asyncio.subprocess.create_subprocess_shell', new_callable=AsyncMock) as mock_create_subprocess_shell:
            mock_process = AsyncMock()
            mock_process.communicate.side_effect = asyncio.TimeoutError
            mock_process.returncode = None # Indicate it didn't finish
            mock_create_subprocess_shell.return_value = mock_process

            with pytest.raises(asyncio.TimeoutError):
                sandbox_instance._run_shell_command(command, timeout=1) # Changed to _run_shell_command

    async def test_run_shell_command_with_file_interaction(self, sandbox_instance):
        """
        Tests a shell command that interacts with files created in the sandbox.
        """
        sandbox_instance._write_file("script.py", "print('Script output')") # Changed to _write_file
        command = "python script.py"
        result = sandbox_instance._run_shell_command(command) # Changed to _run_shell_command

        assert result["stdout"].strip() == "Script output"
        assert result["exit_code"] == 0

    async def test_get_absolute_path(self, sandbox_instance):
        """
        Tests get_absolute_path for various inputs.
        """
        # Relative path
        abs_path = sandbox_instance.get_absolute_path("my_file.txt")
        assert abs_path == str(sandbox_instance.sandbox_path / "my_file.txt")

        # Absolute path (should return as is if within sandbox)
        # Note: This test assumes the sandbox_path is the root for absolute paths.
        # In a real scenario, get_absolute_path might need to validate if the provided
        # absolute path is actually *within* the sandbox. For now, we'll test
        # that it correctly forms an absolute path from a relative one.
        # If the input is already absolute and outside the sandbox, the sandbox
        # should ideally prevent access. This test focuses on path construction.
        
        # For simplicity, let's test with a path that is conceptually "absolute"
        # but still within the sandbox's domain for this test's purpose.
        # The actual security of preventing outside access is handled by the
        # subprocess execution environment, not just path resolution.
        
        # Test with an absolute path that is *inside* the sandbox
        inner_abs_path = sandbox_instance.sandbox_path / "another_file.txt"
        result_path = sandbox_instance.get_absolute_path(str(inner_abs_path))
        assert result_path == str(inner_abs_path)

        # Test with a path that tries to escape the sandbox (should be normalized to stay within)
        # The current implementation of get_absolute_path doesn't explicitly prevent
        # '..' traversal, but the run_shell_command's CWD and potential chroot/jail
        # would handle actual security. For path resolution, it should just normalize.
        escaped_path = "../outside_file.txt"
        resolved_path = sandbox_instance.get_absolute_path(escaped_path)
        # Expect it to resolve relative to sandbox_path, then normalize.
        # The actual security is in the execution of the command.
        assert resolved_path == str((sandbox_instance.sandbox_path / escaped_path).resolve())

    async def test_run_shell_command_working_directory(self, sandbox_instance):
        """
        Tests that shell commands are run within the sandbox's directory.
        """
        # Create a file in a subdirectory
        subdir = sandbox_instance.sandbox_path / "my_subdir"
        subdir.mkdir()
        (subdir / "file_in_subdir.txt").write_text("content")

        # Run a command that lists files in the current directory
        # and then changes to subdir and lists again
        command = "dir && cd my_subdir && dir" if os.name == "nt" else "ls && cd my_subdir && ls"
        result = await sandbox_instance.run_shell_command(command)
        
        # Check if 'file_in_subdir.txt' is listed after changing directory
        assert "file_in_subdir.txt" in result["stdout"]
        assert "file_in_subdir.txt" not in result["stdout"].splitlines()[0] # Should not be in the first 'ls' output

    async def test_run_shell_command_environment_variables(self, sandbox_instance):
        """
        Tests that environment variables can be set for shell commands.
        """
        command = "echo %MY_VAR%" if os.name == "nt" else "echo $MY_VAR"
        env = {"MY_VAR": "custom_value"}
        result = await sandbox_instance.run_shell_command(command, env=env)

        assert result["stdout"].strip() == "custom_value"
        assert result["exit_code"] == 0

    async def test_submit_deliverable(self, sandbox_instance):
        """
        Tests the submit_deliverable method.
        """
        deliverable_name = "source_code.py"
        content = "print('Final code')"
        await sandbox_instance.write_file(deliverable_name, content)

        # submit_deliverable should return the content of the file
        submitted_content = await sandbox_instance.submit_deliverable(deliverable_name)
        assert submitted_content == content

        # Test with a non-existent deliverable
        with pytest.raises(FileNotFoundError):
            await sandbox_instance.submit_deliverable("non_existent_deliverable.txt")

    async def test_submit_deliverable_outside_sandbox(self, sandbox_instance, tmp_path):
        """
        Tests that submit_deliverable prevents access to files outside the sandbox.
        """
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("secret")

        # The sandbox's get_absolute_path should prevent this, or the underlying
        # file read should fail due to path resolution.
        with pytest.raises(ValueError, match="Attempted to access file outside sandbox"):
            await sandbox_instance.submit_deliverable(str(outside_file))

    async def test_read_file_outside_sandbox(self, sandbox_instance, tmp_path):
        """
        Tests that read_file prevents access to files outside the sandbox.
        """
        outside_file = tmp_path / "outside_read.txt"
        outside_file.write_text("secret")

        with pytest.raises(ValueError, match="Attempted to access file outside sandbox"):
            await sandbox_instance.read_file(str(outside_file))

    async def test_write_file_outside_sandbox(self, sandbox_instance, tmp_path):
        """
        Tests that write_file prevents access to files outside the sandbox.
        """
        outside_file = tmp_path / "outside_write.txt"
        with pytest.raises(ValueError, match="Attempted to write file outside sandbox"):
            await sandbox_instance.write_file(str(outside_file), "malicious content")