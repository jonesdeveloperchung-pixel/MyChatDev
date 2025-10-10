"""Configuration settings for the cooperative LLM system."""

from typing import Dict, List
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """Configuration for individual LLM models."""
    name: str
    model_id: str
    role: str
    temperature: float = 0.7
    max_tokens: int = 65536 # Adjust based on model capabilities


class SystemConfig(BaseModel):
    """System-wide configuration."""
    ollama_host: str = "http://localhost:11434"
    max_iterations: int = 5
    quality_threshold: float = 0.8
    change_threshold: float = 0.1
    enable_compression: bool = True
    compression_threshold: int = 32768  # Tokens
    log_level: str = "INFO"

# Available LLM configurations based on your Ollama models
AVAILABLE_LLMS: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(
        name="Product Manager",
        model_id="gemma3:12b",
        role="product_manager",
        temperature=0.3
    ),
    "architect": LLMConfig(
        name="System Architect", 
        model_id="phi4:14b",
        role="architect",
        temperature=0.2
    ),
    "programmer": LLMConfig(
        name="Programmer",
        model_id="gpt-oss:20b",
        role="programmer", 
        temperature=0.1
    ),
    "tester": LLMConfig(
        name="Tester",
        model_id="mistral:7b",
        role="tester",
        temperature=0.2
    ),
    "reviewer": LLMConfig(
        name="Code Reviewer",
        model_id="phi4:14b", 
        role="reviewer",
        temperature=0.3
    )
}

# Default system configuration
DEFAULT_CONFIG = SystemConfig()