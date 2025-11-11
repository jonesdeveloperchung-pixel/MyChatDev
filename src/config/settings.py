from pydantic import BaseModel, ConfigDict
from typing import Dict, Optional
from pathlib import Path

class SystemConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """System configuration for MCP integration"""
    use_mcp_sandbox: bool = False
    mcp_server_host: str = "127.0.0.1"
    mcp_server_port: int = 8000
    sandbox_dir: str = "./sandbox"
    audit_log_path: str = "./audit.log"
    command_whitelist: list = ["python", "node", "cmd", "ls", "dir", "cat", "type"]
    domain_whitelist: list = ["httpbin.org", "jsonplaceholder.typicode.com"]
    quality_threshold: float = 0.7
    change_threshold: float = 0.05
    max_iterations: int = 10
    stagnation_iterations: int = 3
    enable_human_approval: bool = False
    enable_sandbox: bool = False
    enable_compression: bool = False
    compression_threshold: int = 1000
    log_level: str = "INFO"
    ollama_host: str = "http://localhost:11434"
    enable_system_prompt_files: bool = False
    deliverables_path: Path = Path("deliverables")

DEFAULT_CONFIG = SystemConfig()

class LLMConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    """LLM configuration for a specific role."""
    model_id: str
    name: Optional[str] = None
    role: Optional[str] = None
    base_url: str = "http://localhost:11434"
    api_key: str = "ollama"
    temperature: float = 0.7
    timeout: int = 600
    max_tokens: int = 1024

def get_available_llms() -> Dict[str, LLMConfig]:
    """
    Returns a dictionary of default LLM configurations for various roles.
    """
    return {
        "product_manager": LLMConfig(model_id="ollama/llama3", name="Product Manager", role="product_manager"),
        "architect": LLMConfig(model_id="ollama/llama3", name="Architect", role="architect"),
        "programmer": LLMConfig(model_id="ollama/llama3", name="Programmer", role="programmer"),
        "tester": LLMConfig(model_id="ollama/llama3", name="Tester", role="tester"),
        "reviewer": LLMConfig(model_id="ollama/llama3", name="Reviewer", role="reviewer"),
        "quality_gate": LLMConfig(model_id="ollama/llama3", name="Quality Gate", role="quality_gate"),
        "reflector": LLMConfig(model_id="ollama/llama3", name="Reflector", role="reflector"),
        "distiller": LLMConfig(model_id="ollama/llama3", temperature=0.1, name="Distiller", role="distiller"),
    }