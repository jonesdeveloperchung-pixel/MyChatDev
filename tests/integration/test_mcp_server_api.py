import pytest
import httpx
import tempfile
import os
import threading
import time
from mcp_server.mcp_server import MCPServer
from src.config.settings import SystemConfig

class TestMCPServerAPI:
    
    @classmethod
    def setup_class(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.config = SystemConfig(
            sandbox_dir=cls.temp_dir,
            audit_log_path=os.path.join(cls.temp_dir, "audit.log"),
            command_whitelist=["echo", "python", "dir", "ls"],
            mcp_server_port=8001  # Use different port for testing
        )
        cls.server = MCPServer(cls.config)
        
        # Start server in background thread
        cls.server_thread = threading.Thread(
            target=cls.server.run, 
            kwargs={"host": "127.0.0.1", "port": 8001},
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(2)  # Wait for server to start
        
        cls.base_url = "http://127.0.0.1:8001"
    
    def test_valid_write_file_instruction(self):
        """MCP-S-API-001: Valid writeFile instruction"""
        instruction = {
            "action": "write",
            "target": "file",
            "path": "test.txt",
            "content": "hello"
        }
        
        with httpx.Client() as client:
            response = client.post(f"{self.base_url}/mcp", json=instruction)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
    
    def test_valid_read_file_instruction(self):
        """MCP-S-API-002: Valid readFile instruction"""
        # First write a file
        self.test_valid_write_file_instruction()
        
        instruction = {
            "action": "read",
            "target": "file",
            "path": "test.txt"
        }
        
        with httpx.Client() as client:
            response = client.post(f"{self.base_url}/mcp", json=instruction)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert result["content"] == "hello"
    
    def test_valid_execute_instruction(self):
        """MCP-S-API-003: Valid execute instruction"""
        # First write a simple python script
        write_instruction = {
            "action": "write",
            "target": "file",
            "path": "hello.py",
            "content": "print('hello from python')"
        }
        with httpx.Client() as client:
            response = client.post(f"{self.base_url}/mcp", json=write_instruction)
            assert response.status_code == 200
            assert response.json()["status"] == "success"

        instruction = {
            "action": "execute",
            "target": "script",
            "command": "python",
            "args": ["hello.py"]
        }
        
        with httpx.Client() as client:
            response = client.post(f"{self.base_url}/mcp", json=instruction)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "hello" in result["output"]
    
    def test_invalid_action(self):
        """MCP-S-API-004: Invalid action"""
        instruction = {
            "action": "deleteEverything",
            "target": "all"
        }
        
        with httpx.Client() as client:
            response = client.post(f"{self.base_url}/mcp", json=instruction)
            assert response.status_code == 200  # Server handles gracefully
            result = response.json()
            assert result["status"] == "error"
            assert "unsupported" in result["message"].lower()
    
    def test_path_traversal_attempt(self):
        """MCP-S-API-005: Path traversal attempt"""
        instruction = {
            "action": "read",
            "target": "file",
            "path": "../secret.txt"
        }
        
        with httpx.Client() as client:
            response = client.post(f"{self.base_url}/mcp", json=instruction)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "error"
            assert "outside" in result["message"].lower()
    
    def test_non_whitelisted_command(self):
        """MCP-S-API-006: Non-whitelisted command"""
        instruction = {
            "action": "execute",
            "target": "script",
            "command": "rm",
            "args": ["-rf", "/"]
        }
        
        with httpx.Client() as client:
            response = client.post(f"{self.base_url}/mcp", json=instruction)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "error"
            assert "not allowed" in result["message"].lower()
    
    def test_health_endpoint(self):
        """Test server health endpoint"""
        with httpx.Client() as client:
            response = client.get(f"{self.base_url}/health")
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "healthy"