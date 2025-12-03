# config/llm_profiles.py
"""
Centralised definition of all LLM profiles.

Author: Jones Chung

Each profile is a mapping from role name → LLMConfig.
The dictionary `AVAILABLE_LLMS_BY_PROFILE` lets the CLI pick one
by its short key (e.g. "gemma3_phi4_gpt" or "gemma3:4b2").
"""

from typing import Dict
from pathlib import Path # Added for file path handling
import yaml # Added for YAML parsing
import sys # Added for printing warnings

# Import LLMConfig from its module (update the import path if needed)
from .settings import LLMConfig

# Define LLM Configurations for different roles
LLM_CONFIGS_HIGH_REASONING: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(model_id="gemma3:4b", temperature=0.7, max_tokens=2048, name="gemma3:4b", role="product_manager"),
    "architect": LLMConfig(model_id="gemma3:4b", temperature=0.7, max_tokens=2048, name="gemma3:4b", role="architect"),
    "programmer": LLMConfig(model_id="codellama", temperature=0.7, max_tokens=4096, name="CodeLlama", role="programmer"),
    "tester": LLMConfig(model_id="gemma3:4b", temperature=0.7, max_tokens=2048, name="gemma3:4b", role="tester"),
    "reviewer": LLMConfig(model_id="gemma3:4b", temperature=0.7, max_tokens=2048, name="gemma3:4b", role="reviewer"),
    "quality_gate": LLMConfig(model_id="gemma3:4b", temperature=0.5, max_tokens=512, name="gemma3:4b", role="quality_gate"),
    "reflector": LLMConfig(model_id="gemma3:4b", temperature=0.7, max_tokens=2048, name="gemma3:4b", role="reflector"),
    "distiller": LLMConfig(model_id="gemma3:1b", temperature=0.3, max_tokens=256, name="Gemma2B", role="distiller"),
}

LLM_CONFIGS_FAST_LIGHTWEIGHT: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(model_id="gemma3:1b", temperature=0.7, max_tokens=1024, name="Gemma2B", role="product_manager"),
    "architect": LLMConfig(model_id="gemma3:1b", temperature=0.7, max_tokens=1024, name="Gemma2B", role="architect"),
    "programmer": LLMConfig(model_id="gemma3:1b", temperature=0.7, max_tokens=2048, name="Gemma2B", role="programmer"),
    "tester": LLMConfig(model_id="gemma3:1b", temperature=0.7, max_tokens=1024, name="Gemma2B", role="tester"),
    "reviewer": LLMConfig(model_id="gemma3:1b", temperature=0.7, max_tokens=1024, name="Gemma2B", role="reviewer"),
    "quality_gate": LLMConfig(model_id="gemma3:1b", temperature=0.5, max_tokens=256, name="Gemma2B", role="quality_gate"),
    "reflector": LLMConfig(model_id="gemma3:1b", temperature=0.7, max_tokens=1024, name="Gemma2B", role="reflector"),
    "distiller": LLMConfig(model_id="gemma3:1b", temperature=0.3, max_tokens=128, name="Gemma2B", role="distiller"),
}

# Map profile names to their corresponding LLM configurations
AVAILABLE_LLMS_BY_PROFILE: Dict[str, Dict[str, LLMConfig]] = {
    "High_Reasoning": LLM_CONFIGS_HIGH_REASONING,
    "Fast_Lightweight": LLM_CONFIGS_FAST_LIGHTWEIGHT,
}

def load_profile_from_file(file_path: Path) -> Dict[str, LLMConfig]:
    """
    Loads an LLM profile from a specified YAML file.
    The file is expected to define a dictionary where keys are role names
    and values are dictionaries representing LLMConfig parameters. (Moved from src/cli.py)
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Profile file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_configs = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Invalid YAML format in profile file '{file_path}'.") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to read profile file '{file_path}'.") from exc

    if not isinstance(raw_configs, dict):
        raise TypeError(
            f"Profile file '{file_path}' must contain a dictionary at its root."
        )

    loaded_configs: Dict[str, LLMConfig] = {}
    for role, config_data in raw_configs.items():
        if not isinstance(config_data, dict):
            raise TypeError(
                f"Configuration for role '{role}' in '{file_path}' must be a dictionary."
            )
        try:
            # Ensure name and role are present, or default them
            config_data.setdefault('name', role.replace('_', ' ').title())
            config_data.setdefault('role', role)
            loaded_configs[role] = LLMConfig(**config_data)
        except Exception as exc:
            raise ValueError(
                f"Invalid LLMConfig data for role '{role}' in '{file_path}'. "
                f"Details: {exc}"
            ) from exc
    
    return loaded_configs
