import pytest
from unittest.mock import Mock, patch
from src.workflow.mcp_sandbox import MCPSandbox
from src.config.settings import SystemConfig

class TestMCPSandbox:
    
    def setup_method(self):
        self.config = SystemConfig(
            use_mcp_sandbox=True,
            mcp_server_host="127.0.0.1",
            mcp_server_port=8000
        )
        self.mcp_sandbox = MCPSandbox(self.config)
    
    @patch('httpx.Client')
    def test_run_tests_successful(self, mock_client):
        """MCP-C-UT-001: run_tests_in_sandbox successful run"""
        # Mock successful responses
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "output": "All tests passed", "exit_code": 0}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        result = self.mcp_sandbox.run_tests_in_sandbox("print('hello')", "assert True", "python")
        
        assert "Exit code: 0" in result
        assert "All tests passed" in result
        assert mock_client_instance.post.call_count == 3  # write code, write test, execute
    
    @patch('httpx.Client')
    def test_run_tests_compilation_failure(self, mock_client):
        """MCP-C-UT-002: run_tests_in_sandbox compilation failure"""
        # Mock responses: successful writes, failed execution
        responses = [
            {"status": "success"},  # write code
            {"status": "success"},  # write test
            {"status": "error", "message": "Compilation error"}  # execute
        ]
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        def side_effect(*args, **kwargs):
            mock_response.json.return_value = responses.pop(0)
            return mock_response
        
        mock_client_instance = Mock()
        mock_client_instance.post.side_effect = side_effect
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        result = self.mcp_sandbox.run_tests_in_sandbox("invalid code", "test", "c")
        
        assert "Test execution failed" in result
        assert "Compilation error" in result
    
    @patch('httpx.Client')
    def test_execute_tool_write_file(self, mock_client):
        """MCP-C-UT-003: execute_tool_in_sandbox for writeFile"""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "message": "File written"}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        result = self.mcp_sandbox.execute_tool_in_sandbox("writeFile", path="a.txt", content="b")
        
        assert "File written" in result
        
        # Verify correct instruction was sent
        call_args = mock_client_instance.post.call_args
        instruction = call_args[1]['json']
        assert instruction['action'] == 'write'
        assert instruction['target'] == 'file'
        assert instruction['path'] == 'a.txt'
        assert instruction['content'] == 'b'
    
    @patch('httpx.Client')
    def test_execute_tool_execute_command(self, mock_client):
        """MCP-C-UT-004: execute_tool_in_sandbox for execute"""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "output": "a.txt", "exit_code": 0}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance
        
        result = self.mcp_sandbox.execute_tool_in_sandbox("execute", command="ls")
        
        assert "Exit code: 0" in result
        assert "a.txt" in result
        
        # Verify correct instruction was sent
        call_args = mock_client_instance.post.call_args
        instruction = call_args[1]['json']
        assert instruction['action'] == 'execute'
        assert instruction['target'] == 'script'
        assert instruction['command'] == 'ls'