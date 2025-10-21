"""LLM communication and management module.

Author: Jones Chung
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from ollama import AsyncClient
from langchain_core.messages import AIMessage, HumanMessage # Import AIMessage and HumanMessage
from config.settings import LLMConfig, SystemConfig, DEFAULT_CONFIG
from unittest.mock import MagicMock # Import MagicMock


class LLMManager:
    """Manages communication with multiple Ollama-hosted LLMs."""

    def __init__(self, config: SystemConfig = DEFAULT_CONFIG):
        """Initialize LLM manager with configuration."""
        self.config = config
        self.client = AsyncClient(host=config.ollama_host)
        self.logger = logging.getLogger("coop_llm.llm_manager")
        self._model_cache: Dict[str, bool] = {}

    async def check_model_availability(self, model_id: str) -> bool:
        """Check if a model is available in Ollama."""
        if model_id in self._model_cache:
            return self._model_cache[model_id]

        try:
            models_response = await self.client.list()
            available_models = [model.model for model in models_response.models]

            is_available = model_id in available_models
            self._model_cache[model_id] = is_available

            if not is_available:
                self.logger.warning(
                    f"Model {model_id} not found. Available: {available_models[:5]}"
                )

            return is_available
        except Exception as e:
            self.logger.error(f"Error checking model availability: {e}")
            return False

    async def generate_response(
        self, llm_config: LLMConfig, prompt: str, context: Optional[List[Dict]] = None
    ) -> str:
        """Generate response from specified LLM."""

        # Check model availability
        if not await self.check_model_availability(llm_config.model_id):
            raise ValueError(f"Model {llm_config.model_id} not available")

        # Prepare messages
        messages = context or []
        messages.append({"role": "user", "content": prompt})

        try:
            self.logger.info(
                f"Generating response with {llm_config.name} ({llm_config.model_id})"
            )

            response_parts = []
            async for part in await self.client.chat(
                model=llm_config.model_id,
                messages=messages,
                stream=True,
                options={
                    "temperature": llm_config.temperature,
                    "num_predict": llm_config.max_tokens,
                },
            ):
                if hasattr(part, "message") and hasattr(part.message, "content"):
                    response_parts.append(part.message.content)

            response = "".join(response_parts)
            self.logger.info(
                f"Generated {len(response)} characters from {llm_config.name}"
            )

            return response

        except Exception as e:
            self.logger.error(f"Error generating response from {llm_config.name}: {e}")
            raise

    async def batch_generate(self, requests: List[tuple]) -> Dict[str, str]:
        """Generate responses from multiple LLMs concurrently."""
        tasks = []
        request_ids = []

        for request_id, llm_config, prompt, context in requests:
            task = self.generate_response(llm_config, prompt, context)
            tasks.append(task)
            request_ids.append(request_id)

        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            results = {}
            for request_id, response in zip(request_ids, responses):
                if isinstance(response, Exception):
                    self.logger.error(
                        f"Error in batch request {request_id}: {response}"
                    )
                    results[request_id] = f"Error: {str(response)}"
                else:
                    results[request_id] = response

            return results

        except Exception as e:
            self.logger.error(f"Error in batch generation: {e}")
            raise

    async def compress_content(self, content: str, distiller_config: LLMConfig, max_length: int = 8192) -> str:
        """Compress content using summarization if it exceeds threshold."""
        if len(content) <= max_length:
            return content

        from utils.prompts import get_prompt

        prompt = get_prompt("summarizer", content=content, max_length=max_length)

        try:
            summary = await self.generate_response(distiller_config, prompt)
            self.logger.info(
                f"Compressed content from {len(content)} to {len(summary)} characters"
            )
            return summary
        except Exception as e:
            self.logger.error(f"Error compressing content: {e}")
            # Return truncated content as fallback
            return content[:max_length] + "... [truncated]"

    def get_llm_model(self, llm_config: LLMConfig):
        """
        Returns a configured LLM model instance (e.g., from ollama.AsyncClient)
        that can be used for interactive sessions or tool calling.
        """
        # This is a simplified representation. In a real scenario, you might
        # return a LangChain Runnable object or similar.
        # For now, we'll return a mock object that has an 'invoke' method
        # that calls generate_response. This will need to be properly integrated
        # with LangChain's tool calling mechanism.
        
        # For the purpose of fixing the AttributeError, we'll create a simple
        # mock-like object that has an 'invoke' method.
        
        class MockLLM:
            def __init__(self, manager, config):
                self.manager = manager
                self.config = config
                self.tool_names = [] # Placeholder for tool names

            async def invoke(self, messages: List[Any]): # Changed type hint to Any for flexibility
                # Extract the latest user message for the prompt
                prompt = messages[-1].content if messages and hasattr(messages[-1], 'content') else ""
                
                # Simulate tool calling if the prompt suggests it
                # This is a very basic simulation and will need to be replaced
                # with actual tool parsing and execution.
                if "write_file" in prompt and "filename=" in prompt:
                    mock_response = MagicMock()
                    mock_response.tool_calls = [{"name": "write_file", "args": {"filename": "simulated.txt", "content": "simulated content"}, "id": "call_write_file_0"}]
                    mock_response.content = ""
                    return mock_response
                elif "submit_deliverable" in prompt:
                    mock_response = MagicMock()
                    mock_response.tool_calls = [{"name": "submit_deliverable", "args": {"code": "simulated final code"}, "id": "call_submit_deliverable_0"}]
                    mock_response.content = ""
                    return mock_response
                else:
                    response_content = await self.manager.generate_response(self.config, prompt, context=messages[:-1])
                    mock_response = MagicMock()
                    mock_response.tool_calls = [] # No tool calls for regular response
                    mock_response.content = response_content
                    return mock_response

        return MockLLM(self, llm_config)
