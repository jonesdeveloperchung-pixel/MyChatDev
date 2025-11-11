import subprocess
from pathlib import Path
from .context_manager import ContextManager

class ExecEngine:
    """Executes shell commands with security constraints"""
    
    def __init__(self, context_manager: ContextManager, command_whitelist: list):
        self.context_manager = context_manager
        self.command_whitelist = command_whitelist
    
    def execute_command(self, command: str, args: list = None, timeout: int = 30) -> dict:
        """Execute a whitelisted command"""
        try:
            if command not in self.command_whitelist:
                return {"status": "error", "message": f"Command not allowed: {command}"}
            
            cmd_args = [command] + (args or [])
            
            result = subprocess.run(
                cmd_args,
                cwd=self.context_manager.get_context(),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "status": "success",
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            print(f"DEBUG: ExecEngine Exception: {e}", file=__import__('sys').stderr)
            return {"status": "error", "message": f"Execution error: {str(e)}"}