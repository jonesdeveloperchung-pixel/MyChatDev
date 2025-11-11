import pytest
import tempfile
import os
from pathlib import Path
from mcp_server.context_manager import ContextManager

class TestContextManager:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.context_manager = ContextManager(self.temp_dir)
    
    def test_set_valid_context(self):
        """MCP-S-UT-001: Test setting a valid folder context"""
        result = self.context_manager.set_context(self.temp_dir)
        assert result == True
    
    def test_set_invalid_context(self):
        """MCP-S-UT-002: Test setting an invalid or non-existent folder context"""
        result = self.context_manager.set_context("/nonexistent/path")
        assert result == False
    
    def test_prevent_directory_traversal(self):
        """MCP-S-UT-003: Test that path validation prevents directory traversal"""
        result = self.context_manager.validate_path("../../../etc/passwd")
        assert result == False
        
        with pytest.raises(ValueError):
            self.context_manager.get_safe_path("../../../etc/passwd")
    
    def test_validate_safe_path(self):
        """Test that valid paths within context are accepted"""
        result = self.context_manager.validate_path("test.txt")
        assert result == True
        
        safe_path = self.context_manager.get_safe_path("test.txt")
        assert isinstance(safe_path, Path)
        # Just verify the filename is correct - the path validation is tested elsewhere
        assert safe_path.name == "test.txt"