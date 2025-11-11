from ..config.settings import SystemConfig
from .sandbox_interface import SandboxInterface
from .local_sandbox import LocalSandbox
from .mcp_sandbox import MCPSandbox

def get_sandbox_implementation(config: SystemConfig, llm_manager=None, llm_configs=None) -> SandboxInterface:
    """Factory function to create appropriate sandbox implementation"""
    if config.use_mcp_sandbox:
        return MCPSandbox(config, llm_manager, llm_configs)
    else:
        return LocalSandbox(config, llm_manager, llm_configs)