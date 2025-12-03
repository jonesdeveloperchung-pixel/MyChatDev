"""Unit tests for configuration settings functionality.

Tests the SystemConfig and related configuration management.
"""
import pytest
from pathlib import Path
from copy import deepcopy

from src.config.settings import SystemConfig, LLMConfig, DEFAULT_CONFIG


class TestSystemConfig:
    """Test cases for SystemConfig."""

    def test_default_config_values(self):
        """Test that default configuration has expected values."""
        config = SystemConfig()
        
        assert config.ollama_host == "http://localhost:11434"
        assert config.max_iterations == 5
        assert config.quality_threshold == 0.8
        assert config.change_threshold == 0.1
        assert config.log_level == "INFO"
        assert config.enable_sandbox is True
        assert config.enable_human_approval is False

    def test_config_customization(self):
        """Test that configuration can be customized."""
        config = SystemConfig(
            ollama_host="http://192.168.1.100:11434",
            max_iterations=10,
            quality_threshold=0.9,
            log_level="DEBUG"
        )
        
        assert config.ollama_host == "http://192.168.1.100:11434"
        assert config.max_iterations == 10
        assert config.quality_threshold == 0.9
        assert config.log_level == "DEBUG"

    def test_config_validation_quality_threshold(self):
        """Test validation of quality threshold bounds."""
        # Valid values should work
        config = SystemConfig(quality_threshold=0.5)
        assert config.quality_threshold == 0.5
        
        config = SystemConfig(quality_threshold=1.0)
        assert config.quality_threshold == 1.0

    def test_config_validation_change_threshold(self):
        """Test validation of change threshold bounds."""
        # Valid values should work
        config = SystemConfig(change_threshold=0.05)
        assert config.change_threshold == 0.05
        
        config = SystemConfig(change_threshold=0.5)
        assert config.change_threshold == 0.5

    def test_config_validation_max_iterations(self):
        """Test validation of max iterations."""
        # Valid values should work
        config = SystemConfig(max_iterations=1)
        assert config.max_iterations == 1
        
        config = SystemConfig(max_iterations=100)
        assert config.max_iterations == 100

    def test_config_serialization(self):
        """Test that config can be serialized and deserialized."""
        original_config = SystemConfig(
            ollama_host="http://test:11434",
            max_iterations=3,
            quality_threshold=0.75
        )
        
        # Test model_dump (Pydantic serialization)
        config_dict = original_config.model_dump()
        assert isinstance(config_dict, dict)
        assert config_dict["ollama_host"] == "http://test:11434"
        assert config_dict["max_iterations"] == 3
        
        # Test model_dump_json
        config_json = original_config.model_dump_json()
        assert isinstance(config_json, str)
        assert "http://test:11434" in config_json

    def test_default_config_immutability(self):
        """Test that DEFAULT_CONFIG is not accidentally modified."""
        original_host = DEFAULT_CONFIG.ollama_host
        original_iterations = DEFAULT_CONFIG.max_iterations
        
        # Create a copy and modify it
        config_copy = deepcopy(DEFAULT_CONFIG)
        config_copy.ollama_host = "http://modified:11434"
        config_copy.max_iterations = 999
        
        # Verify original is unchanged
        assert DEFAULT_CONFIG.ollama_host == original_host
        assert DEFAULT_CONFIG.max_iterations == original_iterations


class TestLLMConfig:
    """Test cases for LLMConfig."""

    def test_llm_config_creation(self):
        """Test basic LLM config creation."""
        config = LLMConfig(
            name="Test Model",
            model_id="test:latest",
            role="tester"
        )
        
        assert config.name == "Test Model"
        assert config.model_id == "test:latest"
        assert config.role == "tester"
        assert config.temperature == 0.7  # default
        assert config.max_tokens == 131072  # default

    def test_llm_config_customization(self):
        """Test LLM config with custom parameters."""
        config = LLMConfig(
            name="Custom Model",
            model_id="custom:model",
            role="programmer",
            temperature=0.3,
            max_tokens=4096,
            system_prompt="You are a helpful assistant."
        )
        
        assert config.temperature == 0.3
        assert config.max_tokens == 4096
        assert config.system_prompt == "You are a helpful assistant."

    def test_llm_config_validation_temperature(self):
        """Test temperature validation."""
        # Valid temperatures
        config = LLMConfig(name="Test", model_id="test:model", role="test", temperature=0.0)
        assert config.temperature == 0.0
        
        config = LLMConfig(name="Test", model_id="test:model", role="test", temperature=2.0)
        assert config.temperature == 2.0

    def test_llm_config_validation_max_tokens(self):
        """Test max_tokens validation."""
        # Valid max_tokens
        config = LLMConfig(name="Test", model_id="test:model", role="test", max_tokens=1)
        assert config.max_tokens == 1
        
        config = LLMConfig(name="Test", model_id="test:model", role="test", max_tokens=1000000)
        assert config.max_tokens == 1000000

    def test_llm_config_serialization(self):
        """Test LLM config serialization."""
        config = LLMConfig(
            name="Serialization Test",
            model_id="serialize:test",
            role="serializer",
            temperature=0.5
        )
        
        config_dict = config.model_dump()
        assert config_dict["name"] == "Serialization Test"
        assert config_dict["model_id"] == "serialize:test"
        assert config_dict["temperature"] == 0.5


class TestConfigIntegration:
    """Integration tests for configuration components."""

    def test_config_with_paths(self):
        """Test configuration with Path objects."""
        test_path = Path("test/database.sqlite")
        config = SystemConfig(database_url=f"sqlite:///{test_path}")
        
        assert str(test_path) in config.database_url

    def test_config_environment_compatibility(self):
        """Test that config works in different environments."""
        # Test with different log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = SystemConfig(log_level=level)
            assert config.log_level == level

    def test_multiple_llm_configs(self):
        """Test managing multiple LLM configurations."""
        configs = {
            "product_manager": LLMConfig(
                name="PM Model", 
                model_id="gemma3:4b", 
                role="product_manager"
            ),
            "programmer": LLMConfig(
                name="Coder Model", 
                model_id="deepseek-coder:6.7b", 
                role="programmer"
            ),
        }
        
        assert len(configs) == 2
        assert configs["product_manager"].role == "product_manager"
        assert configs["programmer"].role == "programmer"


if __name__ == "__main__":
    pytest.main([__file__])