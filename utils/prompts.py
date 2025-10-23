"""Centralized prompt management for different LLM roles.

Author: Jones Chung
"""

import logging
from typing import Dict
from pathlib import Path

# Define the base path for prompt files
PROMPT_DIR = Path(__file__).parent.parent / "config"

def _read_prompt_file(role: str) -> str:
    """Reads a prompt template from a file in the config directory."""
    file_path = PROMPT_DIR / f"{role}_prompt.txt"
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found for role '{role}': {file_path}")
    content = file_path.read_text(encoding="utf-8")
    logging.getLogger("coop_llm").debug(f"Read prompt for role '{role}' from {file_path}:\n---\n{content}\n---")
    return content

# Cache for loaded prompts to avoid reading from disk multiple times
_PROMPT_CACHE: Dict[str, str] = {}

def get_prompt(role: str, main_content: str = "", **kwargs) -> Dict[str, str]:
    """Get formatted system and user prompts for a specific role."""
    system_template = ""
    user_template = ""

    # Try to read system prompt
    system_file_path = PROMPT_DIR / f"system_{role}_prompt.txt"
    if system_file_path.exists():
        system_template = system_file_path.read_text(encoding="utf-8")
        logging.getLogger("coop_llm").debug(f"Read system prompt for role '{role}' from {system_file_path}:\n---\n{system_template}\n---")

    # Read user prompt
    user_file_path = PROMPT_DIR / f"{role}_prompt.txt"
    logging.getLogger("coop_llm").debug(f"Checking user prompt file: {user_file_path}")
    logging.getLogger("coop_llm").debug(f"User prompt file exists: {user_file_path.exists()}")
    if not user_file_path.exists():
        raise FileNotFoundError(f"User prompt file not found for role '{role}': {user_file_path}")
    user_template = user_file_path.read_text(encoding="utf-8")
    logging.getLogger("coop_llm").debug(f"""Read user prompt for role '{role}' from {user_file_path}:
---
{user_template}
---""")

    # Determine which arguments to pass to format based on template content
    format_args = kwargs.copy()
    if "{main_content}" in user_template:
        format_args["main_content"] = main_content

    formatted_prompts = {
        "system": system_template, # System template for quality_gate does not use kwargs
        "user": user_template.format(**format_args)
    }
    logging.getLogger("coop_llm").debug(f"get_prompt returning: {formatted_prompts}")
    return formatted_prompts