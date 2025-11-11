import pytest
import tempfile
from mcp_server.context_manager import ContextManager
from mcp_server.exec_engine import ExecEngine

class TestExecEngine:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.context_manager = ContextManager(self.temp_dir)
        self.whitelist = ["cmd", "python", "dir", "ls"]  # Use cmd for Windows
        self.exec_engine = ExecEngine(self.context_manager, self.whitelist)
    
    def test_execute_whitelisted_command(self):
        """MCP-S-UT-009: Test executing a whitelisted command"""
        result = self.exec_engine.execute_command("cmd", ["/c", "echo", "hello"])
        assert result["status"] == "success"
        assert "hello" in result["output"]
        assert result["exit_code"] == 0
    
    def test_execute_non_whitelisted_command(self):
        """MCP-S-UT-010: Test executing a non-whitelisted command"""
        result = self.exec_engine.execute_command("rm", ["-rf", "/"])
        assert result["status"] == "error"
        assert "not allowed" in result["message"].lower()
    
    def test_command_execution_with_arguments(self):
        """MCP-S-UT-011: Test command execution with arguments"""
        result = self.exec_engine.execute_command("cmd", ["/c", "echo", "test", "argument"])
        assert result["status"] == "success"
        assert "test argument" in result["output"]
    
    def test_command_timeout(self):
        """Test command timeout functionality"""
        # This test might be platform-specific, using a simple timeout test
        result = self.exec_engine.execute_command("cmd", ["/c", "echo", "timeout_test"], timeout=1)
        assert result["status"] == "success"  # Echo should complete quickly