import os
from pathlib import Path

class ContextManager:
    """Manages and enforces folder scope for all operations"""
    
    def __init__(self, sandbox_dir: str):
        self.sandbox_dir = Path(sandbox_dir).resolve()
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
    
    def set_context(self, path: str) -> bool:
        """Set the folder context"""
        try:
            context_path = Path(path).resolve()
            if self.sandbox_dir in context_path.parents or context_path == self.sandbox_dir:
                return True
            return False
        except Exception:
            return False
    
    def get_context(self) -> str:
        """Get current folder context"""
        return str(self.sandbox_dir)
    
    def validate_path(self, path: str) -> bool:
        """Validate that path is within sandbox context"""
        try:
            full_path = (self.sandbox_dir / path).resolve()
            return self.sandbox_dir in full_path.parents or full_path == self.sandbox_dir
        except Exception:
            return False
    
    def get_safe_path(self, path: str) -> Path:
        """Get safe path within sandbox"""
        if not self.validate_path(path):
            raise ValueError(f"Path {path} is outside allowed context")
        return self.sandbox_dir / path