"""
This module defines the Sandbox environment for executing code and tests.

Author: Jones Chung
"""

import os
import subprocess
from typing import List, Dict, Any

from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage

from models.llm_manager import LLMManager
from config.settings import SystemConfig, LLMConfig

import re
import ast # Add this import at the top

class Sandbox:
    """
    Manages a sandboxed execution environment for the Programmer agent.

    Provides tools for file operations, shell command execution, and test execution
    within an isolated directory. It also orchestrates the interaction with the
    Programmer LLM to iteratively develop and test code.
    """
    def __init__(self, config: SystemConfig, llm_manager: LLMManager, llm_configs: Dict[str, LLMConfig]):
        self.config = config
        self.llm_manager = llm_manager
        self.llm_configs = llm_configs
        self.sandbox_dir = os.path.join(config.deliverables_path, "sandbox")
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.final_code_submission = None # Initialize submission attribute

    def _run_shell_command(self, command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.sandbox_dir,
                check=True
            )
            return result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            return e.stdout + e.stderr + f"Error: {e}"

    def _write_file(self, filename: str, content: str):
        file_path = os.path.join(self.sandbox_dir, filename)
        with open(file_path, "w") as f:
            f.write(content)

    def _read_file(self, filename: str) -> str:
        file_path = os.path.join(self.sandbox_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return f.read()
        return f"File not found: {filename}"

    def _list_directory(self, path: str = ".") -> str:
        full_path = os.path.join(self.sandbox_dir, path)
        if os.path.exists(full_path) and os.path.isdir(full_path):
            return "\n".join(os.listdir(full_path))
        return f"Directory not found: {path}"

    def submit_deliverable(self, code: str) -> str:
        """
        Allows the programmer agent to submit its final code.
        This will be captured by the run_sandbox method.
        """
        self.final_code_submission = code
        return "Deliverable submitted successfully."

    def run_tests_in_sandbox(self, code: str, tests: str, language: str = "c") -> str:
        """
        Writes the provided code and tests to the sandbox, then executes the tests.
        Returns the output of the test execution.
        """
        if not self.config.enable_sandbox:
            return "Sandbox is disabled. Tests not executed."

        # Extract code blocks from the 'tests' string
        # This assumes the LLM provides tests within markdown code blocks
        # Use re.DOTALL to match across newlines
        code_blocks = re.findall(r'```(?:python|c)?\s*\n(.*?)\n```', tests, re.DOTALL)
        
        extracted_tests = ""
        if code_blocks:
            # Concatenate all found code blocks
            extracted_tests = "\n".join([block.strip() for block in code_blocks])
        
        if not extracted_tests.strip():
            return "Error: No executable test code found in LLM response after extraction."

        if language == "python":
            # Validate Python code syntax
            try:
                ast.parse(extracted_tests)
            except SyntaxError as e:
                return f"Error: LLM generated invalid Python test code. SyntaxError: {e}"
            
            code_filename = "main.py"
            test_filename = "test_main.py"
            compile_command = "" # Python doesn't need explicit compilation
            run_command = "pytest test_main.py"
        elif language == "c":
            code_filename = "main.c"
            test_filename = "test_main.c"
            compile_command = "gcc main.c test_main.c -o test_runner"
            run_command = "./test_runner"
        else:
            return f"Unsupported language: {language}"

        # Write the code and extracted tests to files in the sandbox
        self._write_file(code_filename, code)
        self._write_file(test_filename, extracted_tests)

        if compile_command:
            compile_output = self._run_shell_command(compile_command)
            if "error" in compile_output.lower():
                return f"Compilation failed: {compile_output}"

        test_output = self._run_shell_command(run_command)
        return test_output

    def execute_tool_in_sandbox(self, tool_name: str, *args, **kwargs) -> str:
        """
        Executes a specified tool within the sandbox environment.
        This method acts as an interface for other nodes (e.g., Tester) to interact with sandbox tools.
        """
        if tool_name == "run_shell_command":
            return self._run_shell_command(*args, **kwargs)
        elif tool_name == "write_file":
            return self._write_file(*args, **kwargs)
        elif tool_name == "read_file":
            return self._read_file(*args, **kwargs)
        elif tool_name == "list_directory":
            return self._list_directory(*args, **kwargs)
        else:
            return f"Error: Unknown tool '{tool_name}'"

    async def run_sandbox(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if not self.config.enable_sandbox:
            return {"code_implementation": state["code_implementation"]}

        # Initialize the tool-using programmer agent
        programmer_llm_config = self.llm_configs["programmer"]
        programmer_llm = self.llm_manager.get_llm_model(programmer_llm_config)

        # Tools available to the programmer agent
        tools = {
            "write_file": self._write_file,
            "read_file": self._read_file,
            "run_shell_command": self._run_shell_command,
            "list_directory": self._list_directory,
            "submit_deliverable": self.submit_deliverable,
        }

        # Initial prompt for the programmer agent
        initial_prompt_content = f"""You are an expert programmer working in a sandboxed environment.
Your goal is to implement the required functionality and make all tests pass.
You have the following tools available: {list(tools.keys())}.

Here's your workflow:
1. Understand the requirements: {state['requirements']}
2. Understand the tests you need to pass: {state['test_results']}
"""
        if state.get('review_feedback'):
            initial_prompt_content += f"3. Consider the following review feedback from the previous iteration: {state['review_feedback']}\n"
            # Adjust numbering for subsequent steps
            start_step = 4
        else:
            start_step = 3

        if state.get('strategic_guidance'):
            initial_prompt_content += f"{start_step}. Consider the following strategic guidance from the Reflector: {state['strategic_guidance']}\n"
            start_step += 1

        initial_prompt_content += f"{start_step}. Start by writing the source code (e.g., 'main.c') and a 'Makefile' to compile and run your code and tests. Use the 'write_file' tool.\n"
        start_step += 1
        initial_prompt_content += f"{start_step}. Compile your code and tests using 'run_shell_command' (e.g., 'make').\n"
        start_step += 1
        initial_prompt_content += f"{start_step}. If compilation fails, analyze the error output, debug your code, and retry.\n"
        start_step += 1
        initial_prompt_content += f"{start_step}. If compilation succeeds, run the tests using 'run_shell_command' (e.g., 'make test' or './test_runner').\n"
        start_step += 1
        initial_prompt_content += f"{start_step}. If tests fail, analyze the test output, debug your code, and retry the compile-and-test cycle.\n"
        start_step += 1
        initial_prompt_content += f"{start_step}. Once all tests pass, use the 'submit_deliverable' tool to submit your final, working code.\n"
        initial_prompt_content += "Iterate through these steps until all tests pass and you have submitted the deliverable.\n"
        conversation_history = [HumanMessage(content=initial_prompt_content)]
        final_code = ""
        max_iterations = 10  # Limit iterations to prevent infinite loops

        for i in range(max_iterations):
            response = await programmer_llm.invoke(conversation_history)
            conversation_history.append(response)

            if self.final_code_submission:
                final_code = self.final_code_submission
                print(f"Sandbox: Programmer agent submitted final code via submit_deliverable in iteration {i+1}.")
                break

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    try:
                        tool_output = self.execute_tool_in_sandbox(tool_name, **tool_args)
                        conversation_history.append(HumanMessage(content=f"Tool output ({tool_name}): {tool_output}"))
                    except Exception as e:
                        conversation_history.append(HumanMessage(content=f"Error executing tool {tool_name}: {e}"))
            elif response.content:
                # If the agent provides content without a tool call, it might be a message or an attempt to provide code directly
                # For now, we'll treat it as a message and continue, expecting a tool call for submission.
                print(f"Sandbox: Programmer agent provided content without tool call in iteration {i+1}. Content: {response.content[:100]}...")

        if not final_code:
            print("Sandbox: Max iterations reached without final code submission. Returning a placeholder code.")
            final_code = "/* Placeholder code as no final code was submitted by programmer agent. */"

        return {"code_implementation": final_code}