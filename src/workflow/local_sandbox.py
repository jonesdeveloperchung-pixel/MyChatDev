import subprocess
import os
from typing import Dict, Any
from .sandbox_interface import SandboxInterface

class LocalSandbox(SandboxInterface):
    """Local sandbox implementation using direct file operations and subprocess"""
    
    def __init__(self, config, llm_manager=None, llm_configs=None):
        self.config = config
        self.llm_manager = llm_manager
        self.llm_configs = llm_configs
        self.sandbox_dir = config.sandbox_dir
        os.makedirs(self.sandbox_dir, exist_ok=True)

    async def run_sandbox(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrates the execution of the Programmer agent within the sandbox"""
        # Simplified implementation for testing
        return {"status": "success", "message": "Local sandbox executed"}

    def run_tests_in_sandbox(self, code: str, tests: str, language: str) -> str:
        """Runs tests within the sandbox"""
        try:
            # Write code and test files
            code_file = os.path.join(self.sandbox_dir, f"code.{language}")
            test_file = os.path.join(self.sandbox_dir, f"test.{language}")
            
            with open(code_file, 'w') as f:
                f.write(code)
            with open(test_file, 'w') as f:
                f.write(tests)
            
            # Run tests based on language
            if language == "python":
                result = subprocess.run(
                    ["python", test_file], 
                    capture_output=True, 
                    text=True, 
                    cwd=self.sandbox_dir
                )
            else:
                return f"Language {language} not supported"
            
            return f"Exit code: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"

    def execute_tool_in_sandbox(self, tool_name: str, *args, **kwargs) -> str:
        """Executes a specified tool within the sandbox"""
        try:
            if tool_name == "writeFile":
                path = kwargs.get("path", "")
                content = kwargs.get("content", "")
                full_path = os.path.join(self.sandbox_dir, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
                return "File written successfully"
            
            elif tool_name == "readFile":
                path = kwargs.get("path", "")
                full_path = os.path.join(self.sandbox_dir, path)
                with open(full_path, 'r') as f:
                    return f.read()
            
            elif tool_name == "execute":
                command = kwargs.get("command", "")
                args_list = kwargs.get("args", [])
                if command in self.config.command_whitelist:
                    result = subprocess.run(
                        [command] + args_list,
                        capture_output=True,
                        text=True,
                        cwd=self.sandbox_dir
                    )
                    return f"Exit code: {result.returncode}\nOutput: {result.stdout}\nError: {result.stderr}"
                else:
                    return f"Command {command} not allowed"
            
            else:
                return f"Tool {tool_name} not supported"
        except Exception as e:
            return f"Error: {str(e)}"