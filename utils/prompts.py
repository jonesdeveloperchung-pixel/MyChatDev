"""Centralized prompt management for different LLM roles.

Author: Jones Chung
"""

from typing import Dict
from pathlib import Path

# Define the base path for prompt files
PROMPT_DIR = Path(__file__).parent.parent / "config"

def _read_prompt_file(role: str) -> str:
    """Reads a prompt template from a file in the config directory."""
    file_path = PROMPT_DIR / f"{role}_prompt.txt"
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found for role '{role}': {file_path}")
    return file_path.read_text(encoding="utf-8")

# Cache for loaded prompts to avoid reading from disk multiple times
_PROMPT_CACHE: Dict[str, str] = {}

def get_prompt(role: str, **kwargs) -> str:
    """Get formatted prompt for a specific role."""
    if role not in _PROMPT_CACHE:
        _PROMPT_CACHE[role] = _read_prompt_file(role)
    
    template = _PROMPT_CACHE[role]
    return template.format(**kwargs)