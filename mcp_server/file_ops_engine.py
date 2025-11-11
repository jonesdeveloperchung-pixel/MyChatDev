import os
from pathlib import Path
from .context_manager import ContextManager

class FileOpsEngine:
    """Handles all file system operations within sandbox context"""
    
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
    
    def read_file(self, path: str) -> dict:
        """Read file content"""
        try:
            safe_path = self.context_manager.get_safe_path(path)
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"status": "success", "content": content}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except FileNotFoundError:
            return {"status": "error", "message": f"File not found: {path}"}
        except Exception as e:
            return {"status": "error", "message": f"Error reading file: {str(e)}"}
    
    def write_file(self, path: str, content: str) -> dict:
        """Write content to file"""
        try:
            safe_path = self.context_manager.get_safe_path(path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"status": "success", "message": "File written successfully"}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Error writing file: {str(e)}"}
    
    def list_files(self, path: str = ".") -> dict:
        """List files and directories"""
        try:
            safe_path = self.context_manager.get_safe_path(path)
            if not safe_path.exists():
                return {"status": "error", "message": f"Path not found: {path}"}
            
            items = []
            for item in safe_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            return {"status": "success", "items": items}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"Error listing files: {str(e)}"}