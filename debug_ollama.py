"""Debug script to check Ollama API responses."""

import asyncio
from ollama import AsyncClient


async def debug_ollama():
    """Debug Ollama API responses."""
    
    client = AsyncClient(host="http://localhost:11434")
    
    try:
        print("Testing Ollama connection...")
        
        # Test list models
        models = await client.list()
        print(f"Models response type: {type(models)}")
        print(f"Models response: {models}")
        
        if isinstance(models, dict) and 'models' in models:
            print(f"Found {len(models['models'])} models:")
            for i, model in enumerate(models['models'][:3]):  # Show first 3
                print(f"  Model {i}: {model}")
        
        # Test simple chat
        print("\nTesting simple chat...")
        response_parts = []
        async for part in await client.chat(
            model='gemma3:4b',
            messages=[{'role': 'user', 'content': 'Say hello'}],
            stream=True
        ):
            response_parts.append(part)
            if len(response_parts) >= 3:  # Just get first few parts
                break
        
        print(f"Chat response parts: {response_parts}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_ollama())