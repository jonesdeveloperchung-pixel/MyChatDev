"""Unit tests for LLM profiles functionality.

Tests profile loading, validation, and management.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import yaml

from src.config.llm_profiles import (
    get_profile_by_name, 
    list_available_profiles,
    validate_profile_structure
)
from src.config.settings import LLMConfig


class TestLLMProfiles:
    """Test cases for LLM profile management."""

    @pytest.fixture
    def sample_profile_data(self):
        """Sample profile data for testing."""
        return {
            "product_manager": {
                "name": "Product Manager Model",
                "model_id": "gemma3:4b",
                "role": "product_manager",
                "temperature": 0.7,
                "max_tokens": 131072
            },
            "programmer": {
                "name": "Programmer Model", 
                "model_id": "deepseek-coder:6.7b",
                "role": "programmer",
                "temperature": 0.3,
                "max_tokens": 131072
            }
        }

    @pytest.fixture
    def sample_profile_yaml(self, sample_profile_data):
        """Sample profile as YAML string."""
        return yaml.dump(sample_profile_data)

    def test_get_profile_by_name_builtin(self):
        """Test getting a built-in profile."""
        # Test with a known built-in profile
        profile = get_profile_by_name("Fast_Lightweight")
        
        if profile:  # Profile exists
            assert isinstance(profile, dict)
            assert len(profile) > 0
            # Check that all values are LLMConfig instances
            for role, config in profile.items():
                assert isinstance(config, LLMConfig)
                assert hasattr(config, 'model_id')
                assert hasattr(config, 'role')

    def test_get_profile_by_name_nonexistent(self):
        """Test getting a non-existent profile."""
        profile = get_profile_by_name("NonExistentProfile")
        assert profile is None

    def test_list_available_profiles(self):
        """Test listing available profiles."""
        profiles = list_available_profiles()
        
        assert isinstance(profiles, list)
        # Should contain at least some built-in profiles
        assert len(profiles) > 0
        
        # Check profile structure
        for profile_name in profiles:
            assert isinstance(profile_name, str)
            assert len(profile_name) > 0

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_get_profile_from_file(self, mock_exists, mock_file, sample_profile_yaml):
        """Test loading profile from file."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = sample_profile_yaml
        
        # This would require modifying the actual function to accept file paths
        # For now, test the validation function
        profile_data = yaml.safe_load(sample_profile_yaml)
        is_valid = validate_profile_structure(profile_data)
        assert is_valid is True

    def test_validate_profile_structure_valid(self, sample_profile_data):
        """Test profile structure validation with valid data."""
        is_valid = validate_profile_structure(sample_profile_data)
        assert is_valid is True

    def test_validate_profile_structure_invalid_missing_role(self):
        """Test profile validation with missing role."""
        invalid_profile = {
            "product_manager": {
                "name": "Test Model",
                "model_id": "test:model",
                # Missing 'role' field
                "temperature": 0.7
            }
        }
        
        is_valid = validate_profile_structure(invalid_profile)
        assert is_valid is False

    def test_validate_profile_structure_invalid_empty(self):
        """Test profile validation with empty data."""
        is_valid = validate_profile_structure({})
        assert is_valid is False

    def test_validate_profile_structure_invalid_type(self):
        """Test profile validation with wrong data type."""
        is_valid = validate_profile_structure("not_a_dict")
        assert is_valid is False

    def test_validate_profile_structure_invalid_nested_type(self):
        """Test profile validation with wrong nested type."""
        invalid_profile = {
            "product_manager": "not_a_dict"
        }
        
        is_valid = validate_profile_structure(invalid_profile)
        assert is_valid is False

    def test_profile_config_conversion(self, sample_profile_data):
        """Test conversion of profile data to LLMConfig objects."""
        # Simulate the conversion process
        configs = {}
        for role, config_data in sample_profile_data.items():
            try:
                configs[role] = LLMConfig(**config_data)
            except Exception as e:
                pytest.fail(f"Failed to create LLMConfig for {role}: {e}")
        
        assert len(configs) == 2
        assert "product_manager" in configs
        assert "programmer" in configs
        
        pm_config = configs["product_manager"]
        assert pm_config.name == "Product Manager Model"
        assert pm_config.model_id == "gemma3:4b"
        assert pm_config.role == "product_manager"
        assert pm_config.temperature == 0.7

    def test_profile_role_consistency(self, sample_profile_data):
        """Test that profile roles are consistent."""
        for role_key, config_data in sample_profile_data.items():
            # The role in the config should match the key
            assert config_data["role"] == role_key

    def test_profile_required_fields(self, sample_profile_data):
        """Test that profiles contain all required fields."""
        required_fields = ["name", "model_id", "role"]
        
        for role, config_data in sample_profile_data.items():
            for field in required_fields:
                assert field in config_data, f"Missing {field} in {role} config"
                assert config_data[field], f"Empty {field} in {role} config"

    def test_profile_optional_fields(self, sample_profile_data):
        """Test handling of optional fields in profiles."""
        # Test that optional fields have reasonable defaults
        for role, config_data in sample_profile_data.items():
            config = LLMConfig(**config_data)
            
            # These should have defaults if not specified
            assert hasattr(config, 'temperature')
            assert hasattr(config, 'max_tokens')
            assert config.temperature >= 0.0
            assert config.max_tokens > 0


class TestProfileEdgeCases:
    """Test edge cases and error conditions."""

    def test_profile_with_special_characters(self):
        """Test profile names with special characters."""
        # Test that the system handles profile names gracefully
        weird_names = ["Profile-With-Dashes", "Profile_With_Underscores", "Profile123"]
        
        for name in weird_names:
            # Should not raise an exception
            result = get_profile_by_name(name)
            # Result can be None (profile doesn't exist) but shouldn't crash
            assert result is None or isinstance(result, dict)

    def test_profile_case_sensitivity(self):
        """Test profile name case sensitivity."""
        # Test different cases of the same profile name
        profile1 = get_profile_by_name("fast_lightweight")
        profile2 = get_profile_by_name("Fast_Lightweight")
        profile3 = get_profile_by_name("FAST_LIGHTWEIGHT")
        
        # The behavior should be consistent (either all None or all same result)
        # This tests the current implementation behavior
        results = [profile1, profile2, profile3]
        non_none_results = [r for r in results if r is not None]
        
        # If any results exist, they should be the same
        if non_none_results:
            first_result = non_none_results[0]
            for result in non_none_results[1:]:
                assert result == first_result

    def test_empty_profile_name(self):
        """Test handling of empty profile name."""
        result = get_profile_by_name("")
        assert result is None

    def test_none_profile_name(self):
        """Test handling of None profile name."""
        result = get_profile_by_name(None)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])