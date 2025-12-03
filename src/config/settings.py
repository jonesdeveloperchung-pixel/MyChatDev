from pydantic import BaseModel, ConfigDict
from typing import Dict, Optional
from pathlib import Path
import yaml # Added for config management
import re   # Added for URL validation
import sys # Added for config management (stderr)


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
    database_url: str = "sqlite:///./data/db.sqlite" # URL for the SQLite database. Defaults to a local file.

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


# ---------- Config Command Functions (Moved from src/cli.py) --------------------
USER_CONFIG_FILE = Path.home() / ".coopllm" / "config.yaml"
USER_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_user_config() -> SystemConfig:
    """
    Loads user-defined SystemConfig from ~/.coopllm/config.yaml, merging with DEFAULT_CONFIG.
    """
    user_config_data = {}
    if USER_CONFIG_FILE.is_file():
        try:
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_config_data = yaml.safe_load(f)
            if not isinstance(user_config_data, dict):
                print(f"Warning: User config file '{USER_CONFIG_FILE}' is not a valid YAML dictionary. Using default config.", file=sys.stderr)
                user_config_data = {}
        except yaml.YAMLError as exc:
            print(f"Warning: Invalid YAML format in user config file '{USER_CONFIG_FILE}': {exc}. Using default config.", file=sys.stderr)
            user_config_data = {}
        except Exception as exc:
            print(f"Warning: Failed to read user config file '{USER_CONFIG_FILE}': {exc}. Using default config.", file=sys.stderr)
            user_config_data = {}
    
    # Merge user config with default config
    # Pydantic's parse_obj_as or direct instantiation handles defaults well
    return SystemConfig(**{**DEFAULT_CONFIG.model_dump(), **user_config_data})

def save_user_config(config: SystemConfig):
    """
    Saves the current SystemConfig to ~/.coopllm/config.yaml.
    """
    try:
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            config_dict = config.model_dump()
            # Ensure Path objects are converted to string for YAML serialization
            if 'deliverables_path' in config_dict and isinstance(config_dict['deliverables_path'], Path):
                config_dict['deliverables_path'] = str(config_dict['deliverables_path'])
            yaml.safe_dump(config_dict, f, indent=2)
            # print(f"Configuration saved to '{USER_CONFIG_FILE}'.") # Removed print, will be handled by CLI/API
    except Exception as e:
        print(f"Error saving configuration to '{USER_CONFIG_FILE}': {e}", file=sys.stderr)
        sys.exit(1)

def normalize_ollama_url(url_string: str) -> str:
    """
    Normalizes an Ollama URL string by ensuring it has a scheme (http://)
    and a default port (11434) if not specified. (Moved from src/cli.py)
    """
    # Basic URL validation regex (simplified)
    url_pattern = re.compile(r"^https?://[a-zA-Z0-9.-]+(?::\d{1,5})?(?:/.*)?$")
    if not url_pattern.match(url_string):
        raise ValueError(f"Invalid URL format: {url_string}")

    # Ensure scheme is present
    if not url_string.startswith("http://") and not url_string.startswith("https://"):
        url_string = f"http://{url_string}"

    # Check if a port is specified. If not, append the default Ollama port.
    # This is a simple check and might not cover all edge cases, but should work for IP:Port and IP.
    # We look for a colon AFTER the scheme part.
    if ":" not in url_string.split("//", 1)[-1]:
        url_string = f"{url_string}:11434"  # Default Ollama port

    return url_string

# Path for user-defined LLM profiles
USER_PROFILES_DIR = Path.home() / ".coopllm" / "profiles"
USER_PROFILES_DIR.mkdir(parents=True, exist_ok=True) # Ensure the directory exists