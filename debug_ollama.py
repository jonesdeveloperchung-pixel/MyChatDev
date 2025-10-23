"""Debug script to check Ollama API responses."""

import asyncio
import argparse
from datetime import datetime
from ollama import AsyncClient


async def debug_ollama(ollama_host: str):
    """Debug Ollama API responses."""

    client = AsyncClient(host=ollama_host)

    try:
        print("Testing Ollama connection...")

        # Test list models
        models_response = await client.list()
        print(f"\n--- Ollama Models ({ollama_host}) ---")
        if models_response and models_response.get("models"):
            print(f"Found {len(models_response["models"])} models:")
            for model_obj in models_response["models"]:
                name = model_obj.model  # Access the 'model' attribute directly
                size_bytes = model_obj.size
                size_mb = size_bytes / (1024 * 1024)
                modified_at = model_obj.modified_at
                print(f"  - Name: {name}, Size: {size_mb:.2f} MB, Last Modified: {modified_at}")
        else:
            print("No models found or unexpected response format.")

        # Test simple chat
        print("\n--- Simple Chat Test ---")
        full_response_content = ""
        try:
            async for part in await client.chat(
                model="gemma3:4b", # Using a common model for testing
                messages=[{"role": "user", "content": "Say hello"}],
                stream=True,
            ):
                if part.get("message") and part["message"].get("content"):
                    content_chunk = part["message"]["content"]
                    full_response_content += content_chunk
                    print(f"  Received: {content_chunk}", end='') # Print chunks as they arrive
            print("\n  Full response: " + full_response_content.strip())
        except Exception as chat_e:
            print(f"Error during chat test: {chat_e}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debug Ollama API connection and models.")
    parser.add_argument("-O", "--ollama_url", type=str, default="http://localhost:11434",
                        help="URL of the Ollama host (e.g., http://localhost:11434)")
    args = parser.parse_args()
    asyncio.run(debug_ollama(args.ollama_url))
