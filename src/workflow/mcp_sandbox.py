import httpx
import json
from typing import Dict, Any
from .sandbox_interface import SandboxInterface
from src.utils.prompts import get_prompt

class MCPSandbox(SandboxInterface):
    """MCP client sandbox implementation"""
    
    def __init__(self, config, llm_manager=None, llm_configs=None):
        self.config = config
        self.llm_manager = llm_manager
        self.llm_configs = llm_configs
        self.server_url = f"http://{config.mcp_server_host}:{config.mcp_server_port}"
    
    def _send_instruction(self, instruction: dict) -> dict:
        """Send instruction to MCP server"""
        try:
            with httpx.Client() as client:
                response = client.post(f"{self.server_url}/mcp", json=instruction, timeout=60.0) # Increased timeout
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"status": "error", "message": f"MCP communication error: {str(e)}"}
    
    async def run_sandbox(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrates the execution of the Programmer agent within the sandbox"""
        
        # 1. Get programmer LLM config and create prompt
        llm_config = self.llm_configs["programmer"]
        combined_content = f"Requirements:\n{state['requirements']}\n\nSystem Design:\n{state['design']}"
        prompt_parts = get_prompt("programmer", main_content=combined_content, system_config=self.config, context=f"Iteration: {state['iteration_count']}")
        messages = []
        if prompt_parts.get("system"):
            messages.append({"role": "system", "content": prompt_parts["system"]})
        messages.append({"role": "user", "content": prompt_parts["user"]})

        # 2. Generate code
        generated_code = await self.llm_manager.generate_response(llm_config, messages)

        # 3. Write code to file in sandbox
        write_instruction = {
            "action": "write",
            "target": "file",
            "path": "generated_code.py",
            "content": generated_code,
            "llm_intent": "write generated code to file"
        }
        write_result = self._send_instruction(write_instruction)
        if write_result.get("status") != "success":
            return {"status": "error", "message": f"Failed to write code to sandbox: {write_result.get('message')}"}

        # 4. Execute code in sandbox
        execute_instruction = {
            "action": "execute",
            "target": "script",
            "command": "python",
            "path": "generated_code.py",
            "llm_intent": "execute generated code"
        }
        execute_result = self._send_instruction(execute_instruction)

        # 5. Return results
        return {
            "status": "success",
            "mcp_result": execute_result,
            "code_implementation": generated_code
        }
    
    def run_tests_in_sandbox(self, code: str, tests: str, language: str) -> str:
        """Runs tests within the sandbox via MCP"""
        try:
            # Write code file
            code_instruction = {
                "action": "write",
                "target": "file",
                "path": f"code.{language}",
                "content": code,
                "llm_intent": "write code file for testing"
            }
            code_result = self._send_instruction(code_instruction)
            
            if code_result.get("status") != "success":
                return f"Failed to write code: {code_result.get('message', 'Unknown error')}"
            
            # Write test file
            test_instruction = {
                "action": "write",
                "target": "file",
                "path": f"test.{language}",
                "content": tests,
                "llm_intent": "write test file"
            }
            test_result = self._send_instruction(test_instruction)
            
            if test_result.get("status") != "success":
                return f"Failed to write tests: {test_result.get('message', 'Unknown error')}"
            
            # Execute tests
            exec_instruction = {
                "action": "execute",
                "target": "script",
                "command": "python" if language == "python" else language,
                "args": [f"test.{language}"],
                "llm_intent": "run tests"
            }
            exec_result = self._send_instruction(exec_instruction)
            
            if exec_result.get("status") == "success":
                return f"Exit code: {exec_result.get('exit_code', 0)}\nOutput: {exec_result.get('output', '')}\nError: {exec_result.get('error', '')}"
            else:
                return f"Test execution failed: {exec_result.get('message', 'Unknown error')}"
                
        except Exception as e:
            return f"Error in run_tests_in_sandbox: {str(e)}"
    
    def execute_tool_in_sandbox(self, tool_name: str, *args, **kwargs) -> str:
        """Executes a specified tool within the sandbox via MCP"""
        try:
            if tool_name == "writeFile":
                instruction = {
                    "action": "write",
                    "target": "file",
                    "path": kwargs.get("path", ""),
                    "content": kwargs.get("content", ""),
                    "llm_intent": f"execute tool: {tool_name}"
                }
            elif tool_name == "readFile":
                instruction = {
                    "action": "read",
                    "target": "file",
                    "path": kwargs.get("path", ""),
                    "llm_intent": f"execute tool: {tool_name}"
                }
            elif tool_name == "execute":
                instruction = {
                    "action": "execute",
                    "target": "script",
                    "command": kwargs.get("command", ""),
                    "args": kwargs.get("args", []),
                    "llm_intent": f"execute tool: {tool_name}"
                }
            else:
                return f"Tool {tool_name} not supported by MCP sandbox"
            
            result = self._send_instruction(instruction)
            
            if result.get("status") == "success":
                if tool_name == "readFile":
                    return result.get("content", "")
                elif tool_name == "execute":
                    return f"Exit code: {result.get('exit_code', 0)}\nOutput: {result.get('output', '')}"
                else:
                    return result.get("message", "Success")
            else:
                return f"Error: {result.get('message', 'Unknown error')}"
                
        except Exception as e:
            return f"Error in execute_tool_in_sandbox: {str(e)}"