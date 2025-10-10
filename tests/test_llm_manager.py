"""Unit tests for LLM Manager functionality."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from models.llm_manager import LLMManager
from config.settings import LLMConfig, SystemConfig

class TestLLMManager:
    """Test cases for LLM Manager."""
    
    @pytest.fixture
    def llm_config(self):
        """Sample LLM configuration for testing.
        
        Provides a pre-configured LLMConfig object for tests.
        """
        return LLMConfig(
            name="Test Model",
            model_id="test:model",
            role="tester",
            temperature=0.5
        )
    
    @pytest.fixture
    def system_config(self):
        """Sample system configuration for testing.
        
        Provides a pre-configured SystemConfig object for tests.
        """
        return SystemConfig(
            ollama_host="http://localhost:11434",
            max_iterations=3
        )
    
    @pytest.fixture
    def llm_manager(self, system_config):
        """LLM Manager instance for testing.
        
        Creates an instance of LLMManager with a given system configuration.
        """
        return LLMManager(system_config)
    
    @pytest.mark.asyncio
    async def test_check_model_availability_success(self, llm_manager):
        """Test successful model availability check.
        
        Verifies that check_model_availability returns True when the model is found.
        """
        
        # Mock the client response to simulate a successful availability check.
        mock_response = {
            'models': [
                {'name': 'test:model'},
                {'name': 'other:model'}
            ]
        }
        
        # Patch the client's list method to return the mock response.
        with patch.object(llm_manager.client, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_response
            
            # Call the method being tested and assert the result.
            result = await llm_manager.check_model_availability("test:model")
            
            assert result is True
            # Verify that the client's list method was called.
            mock_list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_model_availability_not_found(self, llm_manager):
        """Test model not found scenario.
        
        Verifies that check_model_availability returns False when the model is not found.
        """
        
        mock_response = {
            'models': [
                {'name': 'other:model'}
            ]
        }
        
        with patch.object(llm_manager.client, 'list', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_response
            
            result = await llm_manager.check_model_availability("test:model")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, llm_manager, llm_config):
        """Test successful response generation.
        
        Verifies that generate_response works correctly when the model is available.
        """
        
        # Mock model availability check to always return True.
        with patch.object(llm_manager, 'check_model_availability', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = True
            
            # Mock the chat response to simulate a successful chat operation.
            mock_response_parts = [
                {'message': {'content': 'Hello '}},
                {'message': {'content': 'World!'}}
            ]
            
            # Define a mock chat method to return the mock response parts.
            async def mock_chat(*args, **kwargs):
                for part in mock_response_parts:
                    yield part
            
            # Patch the client's chat method to return the mock chat method.
            with patch.object(llm_manager.client, 'chat', new_callable=AsyncMock) as mock_chat_method:
                mock_chat_method.return_value = mock_chat()
                
                # Call the method being tested and assert the result.
                result = await llm_manager.generate_response(llm_config, "Test prompt")
                
                assert result == "Hello World!"
                mock_check.assert_called_once_with(llm_config.model_id)
    
    @pytest.mark.asyncio
    async def test_generate_response_model_unavailable(self, llm_manager, llm_config):
        """Test response generation with unavailable model.
        
        Verifies that generate_response raises a ValueError when the model is unavailable.
        """
        
        with patch.object(llm_manager, 'check_model_availability', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = False
            
            # Assert that generate_response raises a ValueError when the model is unavailable.
            with pytest.raises(ValueError, match="Model .* not available"):
                await llm_manager.generate_response(llm_config, "Test prompt")
    
    @pytest.mark.asyncio
    async def test_batch_generate_success(self, llm_manager, llm_config):
        """Test successful batch generation.
        
        Verifies that batch_generate correctly calls generate_response for each request
        and returns the expected results.
        """
        
        requests = [
            ("req1", llm_config, "Prompt 1", None),
            ("req2", llm_config, "Prompt 2", None)
        ]
        
        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = ["Response 1", "Response 2"]
            
            results = await llm_manager.batch_generate(requests)
            
            assert results == {
                "req1": "Response 1",
                "req2": "Response 2"
            }
            assert mock_generate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_compress_content_no_compression_needed(self, llm_manager):
        """Test content compression when not needed.
        
        Verifies that compress_content returns the original content if it's short enough.
        """
        
        short_content = "This is short content"
        result = await llm_manager.compress_content(short_content, max_length=1000)
        
        assert result == short_content
    
    @pytest.mark.asyncio
    async def test_compress_content_compression_needed(self, llm_manager):
        """Test content compression when needed.
        
        Verifies that compress_content calls generate_response when compression is needed
        and returns the compressed content.
        """
        
        long_content = "This is very long content " * 100
        
        with patch.object(llm_manager, 'generate_response', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = "Compressed content"
            
            result = await llm_manager.compress_content(long_content, max_length=100)
            
            assert result == "Compressed content"
            mock_generate.assert_called_once()

def test_llm_config_validation():
    """Test LLM configuration validation.
    
    Checks that LLMConfig is properly initialized and fields have expected default values.
    """
    
    # Valid configuration
    config = LLMConfig(
        name="Test",
        model_id="test:model",
        role="tester"
    )
    
    assert config.name == "Test"
    assert config.temperature == 0.7  # default value
    assert config.max_tokens == 2000  # default value

def test_system_config_defaults():
    """Test system configuration defaults.
    
    Checks that SystemConfig is properly initialized and fields have expected default values.
    """
    
    config = SystemConfig()
    
    assert config.ollama_host == "http://localhost:11434"
    assert config.max_iterations == 5
    assert config.quality_threshold == 0.8
    assert config.change_threshold == 0.1

if __name__ == "__main__":
    pytest.main([__file__])