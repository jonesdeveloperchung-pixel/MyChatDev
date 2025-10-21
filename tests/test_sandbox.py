"""Unit tests for Sandbox functionality.

Author: Jones Chung
"""
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock

from config.settings import LLMConfig, SystemConfig
from models.llm_manager import LLMManager
from workflow.sandbox import Sandbox


class TestSandbox:
    """Test cases for Sandbox."""

    @pytest.fixture
    def system_config(self, tmp_path):
        """Sample system configuration for testing."""
        return SystemConfig(
            ollama_host="http://localhost:11434",
            max_iterations=3,
            deliverables_path=str(tmp_path),  # Use a temporary directory for deliverables
            enable_sandbox=True,
        )

    @pytest.fixture
    def llm_config(self):
        """Sample LLM configuration for testing."""
        return LLMConfig(
            name="Test Programmer", model_id="test:programmer", role="programmer", temperature=0.5
        )

    @pytest.fixture
    def llm_manager(self, system_config):
        """LLM Manager instance for testing."""
        return LLMManager(system_config)

    @pytest.fixture
    def sandbox(self, system_config, llm_manager, llm_config):
        """Sandbox instance for testing."""
        # Mock llm_manager.get_llm to return a mock LLM
        with patch.object(llm_manager, 'get_llm_model', return_value=MagicMock()) as mock_get_llm_model: # Corrected method name
            sandbox_instance = Sandbox(system_config, llm_manager, {"programmer": llm_config})
            yield sandbox_instance

    @pytest.mark.asyncio
    async def test_run_shell_command_success(self, sandbox):
        """Test successful shell command execution."""
        command = "echo hello"
        output = sandbox._run_shell_command(command)
        assert "hello" in output

    @pytest.mark.asyncio
    async def test_run_shell_command_error(self, sandbox):
        """Test shell command execution with error."""
        command = "exit 1"
        output = sandbox._run_shell_command(command)
        assert "Error" in output  # Expecting "Error" in the output for CalledProcessError

    @pytest.mark.asyncio
    async def test_write_and_read_file(self, sandbox):
        """Test writing content to a file and then reading it back."""
        filename = "test_file.txt"
        content = "This is a test file content."
        sandbox._write_file(filename, content)
        read_content = sandbox._read_file(filename)
        assert read_content == content

    @pytest.mark.asyncio
    async def test_read_non_existent_file(self, sandbox):
        """Test reading a non-existent file."""
        filename = "non_existent_file.txt"
        read_content = sandbox._read_file(filename)
        assert "File not found" in read_content

    @pytest.mark.asyncio
    async def test_list_directory_empty(self, sandbox):
        """Test listing an empty directory."""
        # The sandbox_dir is created by the fixture, so it should be empty initially
        output = sandbox._list_directory()
        assert output == ""

    @pytest.mark.asyncio
    async def test_list_directory_with_files(self, sandbox):
        """Test listing a directory with files."""
        sandbox._write_file("file1.txt", "content1")
        sandbox._write_file("file2.txt", "content2")
        output = sandbox._list_directory()
        assert "file1.txt" in output
        assert "file2.txt" in output

    @pytest.mark.asyncio
    async def test_list_non_existent_directory(self, sandbox):
        """Test listing a non-existent directory."""
        output = sandbox._list_directory("non_existent_dir")
        assert "Directory not found" in output

    @pytest.mark.asyncio
    async def test_execute_tool_in_sandbox(self, sandbox):
        """Test executing various tools via execute_tool_in_sandbox."""
        # Test run_shell_command
        output = sandbox.execute_tool_in_sandbox("run_shell_command", command="echo test_tool_cmd")
        assert "test_tool_cmd" in output

        # Test write_file and read_file
        sandbox.execute_tool_in_sandbox("write_file", filename="tool_file.txt", content="tool content")
        content = sandbox.execute_tool_in_sandbox("read_file", filename="tool_file.txt")
        assert content == "tool content"

        # Test list_directory
        output = sandbox.execute_tool_in_sandbox("list_directory")
        assert "tool_file.txt" in output

        # Test unknown tool
        output = sandbox.execute_tool_in_sandbox("unknown_tool")
        assert "Unknown tool" in output

    @pytest.mark.asyncio
    async def test_run_tests_in_sandbox_success(self, sandbox):
        """Test successful test execution in sandbox."""
        code = "int main() { return 0; }"
        tests = "int test_main() { return 0; }"
        with patch.object(sandbox, '_run_shell_command') as mock_run_shell_command:
            mock_run_shell_command.side_effect = ["", ""]
            output = sandbox.run_tests_in_sandbox(code, tests)
            assert output == ""
            assert mock_run_shell_command.call_count == 2

    @pytest.mark.asyncio
    async def test_run_tests_in_sandbox_compile_error(self, sandbox):
        """Test test execution with compilation error in sandbox."""
        code = "invalid code"
        tests = "int test_main() { return 0; }"
        with patch.object(sandbox, '_run_shell_command') as mock_run_shell_command:
            mock_run_shell_command.side_effect = ["compilation error", ""]
            output = sandbox.run_tests_in_sandbox(code, tests)
            assert "Compilation failed" in output

    @pytest.mark.asyncio
    async def test_run_tests_in_sandbox_runtime_error(self, sandbox):
        """Test test execution with runtime error in sandbox."""
        code = "int main() { return 1; }"
        tests = "int test_main() { return 0; }"
        with patch.object(sandbox, '_run_shell_command') as mock_run_shell_command:
            mock_run_shell_command.side_effect = ["", "runtime error"]
            output = sandbox.run_tests_in_sandbox(code, tests)
            assert "runtime error" in output

    @pytest.mark.asyncio
    async def test_submit_deliverable(self, sandbox):
        """Test submitting a deliverable."""
        code = "final code"
        response = sandbox.submit_deliverable(code)
        assert response == "Deliverable submitted successfully."
        assert sandbox.final_code_submission == code

    @pytest.mark.asyncio
    async def test_run_sandbox_with_submit_deliverable(self, sandbox, llm_manager, llm_config):
        """Test run_sandbox when the LLM agent calls submit_deliverable."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = [
            MagicMock(tool_calls=[{"name": "write_file", "args": {"filename": "main.c", "content": "test code"}}]),
            MagicMock(tool_calls=[{"name": "submit_deliverable", "args": {"code": "final test code"}}]),
        ]
        with patch.object(llm_manager, 'get_llm_model', return_value=mock_llm):
            state = {"requirements": "test reqs", "test_results": "test results"}
            result = await sandbox.run_sandbox(state)
            assert result["code_implementation"] == "final test code"
            assert mock_llm.invoke.call_count == 2

if __name__ == "__main__":
    pytest.main([__file__])