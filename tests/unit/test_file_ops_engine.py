import pytest
import tempfile
import os
from mcp_server.context_manager import ContextManager
from mcp_server.file_ops_engine import FileOpsEngine

class TestFileOpsEngine:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.context_manager = ContextManager(self.temp_dir)
        self.file_ops = FileOpsEngine(self.context_manager)
    
    def test_read_file_within_context(self):
        """MCP-S-UT-004: Test reading a file within the context"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        result = self.file_ops.read_file("test.txt")
        assert result["status"] == "success"
        assert result["content"] == "test content"
    
    def test_read_file_outside_context(self):
        """MCP-S-UT-005: Test reading a file outside the context"""
        result = self.file_ops.read_file("../../../etc/passwd")
        assert result["status"] == "error"
        assert "outside" in result["message"].lower()
    
    def test_write_file_within_context(self):
        """MCP-S-UT-006: Test writing a file within the context"""
        result = self.file_ops.write_file("new_file.txt", "new content")
        assert result["status"] == "success"
        
        # Verify file was created
        test_file = os.path.join(self.temp_dir, "new_file.txt")
        assert os.path.exists(test_file)
        with open(test_file, 'r') as f:
            assert f.read() == "new content"
    
    def test_write_file_outside_context(self):
        """MCP-S-UT-007: Test writing a file outside the context"""
        result = self.file_ops.write_file("../../../tmp/malicious.txt", "bad content")
        assert result["status"] == "error"
        assert "outside" in result["message"].lower()
    
    def test_list_files_within_context(self):
        """MCP-S-UT-008: Test listing files and directories within the context"""
        # Create test files
        os.makedirs(os.path.join(self.temp_dir, "subdir"))
        with open(os.path.join(self.temp_dir, "file1.txt"), 'w') as f:
            f.write("content1")
        
        result = self.file_ops.list_files(".")
        assert result["status"] == "success"
        assert len(result["items"]) >= 2
        
        names = [item["name"] for item in result["items"]]
        assert "subdir" in names
        assert "file1.txt" in names