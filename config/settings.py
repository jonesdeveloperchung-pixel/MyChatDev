"""Configuration settings for the cooperative LLM system.

Author: Jones Chung
"""

from typing import Dict, List
from pathlib import Path
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """Configuration for individual LLM models."""
    model_config = {'protected_namespaces': ()}

    name: str
    model_id: str
    role: str
    temperature: float = 0.7
    max_tokens: int = 131071  # Adjust based on model capabilities


class SystemConfig(BaseModel):
    """System-wide configuration."""

    ollama_host: str = "http://localhost:11434"  # Default Ollama server address
    max_iterations: int = 5
    quality_threshold: float = 0.8
    change_threshold: float = 0.1
    log_level: str = "INFO"
    deliverables_path: Path = Path("deliverables")

    # Sandbox Settings
    enable_sandbox: bool = False

    # Compression Settings
    enable_compression: bool = True
    compression_threshold: int = 65535
    compression_strategy: str = 'progressive_distillation'
    max_compression_ratio: float = 0.5
    compression_chunk_size: int = 8192

    # Stagnation Detection
    stagnation_iterations: int = 3 # Number of iterations to check for stagnation

    # Human Approval
    enable_human_approval: bool = False # Master switch for human approval step

    # System Prompt Management
    enable_system_prompt_files: bool = False # If True, system prompts are read from files; otherwise, internal defaults are used.

    # Mockup Generation
    enable_mockup_generation: bool = False # If True, generates mockup data for debugging graph nodes.


# Default system configuration
DEFAULT_CONFIG = SystemConfig()