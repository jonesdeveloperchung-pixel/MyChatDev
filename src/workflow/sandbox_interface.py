from abc import ABC, abstractmethod
from typing import Dict, Any

class SandboxInterface(ABC):
    """
    Abstract interface for a sandboxed execution environment.
    """

    @abstractmethod
    async def run_sandbox(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates the execution of the Programmer agent within the sandbox.
        """
        pass

    @abstractmethod
    def run_tests_in_sandbox(self, code: str, tests: str, language: str) -> str:
        """
        Runs tests within the sandbox.
        """
        pass

    @abstractmethod
    def execute_tool_in_sandbox(self, tool_name: str, *args, **kwargs) -> str:
        """
        Executes a specified tool within the sandbox.
        """
        pass