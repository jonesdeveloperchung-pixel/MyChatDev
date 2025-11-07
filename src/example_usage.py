import asyncio
from workflow.graph_workflow import GraphWorkflow
from config.settings import DEFAULT_CONFIG, SystemConfig
from config.llm_profiles import AVAILABLE_LLMS_BY_PROFILE

async def main():
    print("🚀 Starting a quick demonstration of the Cooperative LLM System...")

    # 1. Define a simple user prompt for a quick task
    user_input = """Write a Python function that takes two numbers as input and returns their sum. Include a simple example of how to use the function."""
    print(f"\nUser Prompt: {user_input}")

    # 2. Select a lightweight LLM profile for faster execution
    # The 'Low_Reasoning' profile uses smaller models like tinyllama for most roles.
    llm_configs = AVAILABLE_LLMS_BY_PROFILE['Low_Reasoning']
    print(f"Using LLM Profile: Low_Reasoning (using models like {llm_configs['product_manager'].model_id})")

    # 3. Configure system settings for a quick demo
    #    - max_iterations=1: Run only one iteration to get a basic output quickly.
    #    - enable_sandbox=False: Skip the sandboxed development environment.
    #    - enable_human_approval=False: Skip human intervention steps.
    custom_config = SystemConfig(
        ollama_host=DEFAULT_CONFIG.ollama_host,
        max_iterations=1, # Limit to 1 iteration for a quick demo
        quality_threshold=0.0, # Don't halt on quality for a quick demo
        change_threshold=0.0, # Don't trigger reflection for a quick demo
        log_level="INFO", # Keep logging concise for demo
        enable_sandbox=False, # Disable sandbox for faster demo
        enable_human_approval=False, # Disable human approval for faster demo
        # Keep other settings as default
        enable_compression=DEFAULT_CONFIG.enable_compression,
        compression_threshold=DEFAULT_CONFIG.compression_threshold,
        compression_strategy=DEFAULT_CONFIG.compression_strategy,
        max_compression_ratio=DEFAULT_CONFIG.max_compression_ratio,
        compression_chunk_size=DEFAULT_CONFIG.compression_chunk_size,
        stagnation_iterations=DEFAULT_CONFIG.stagnation_iterations,
    )
    print("System configured for a quick demonstration (1 iteration, no sandbox, no human approval).")

    # 4. Initialize and run the workflow
    workflow = GraphWorkflow(custom_config, llm_configs)
    print("\nExecuting workflow...")
    final_state_dict = await workflow.run(user_input)
    print("Workflow execution completed.")

    # 5. Display key deliverables
    print("\n--- Demonstration Results ---")
    print("Requirements:")
    print(final_state_dict.get('requirements', 'N/A'))
    print("\nDesign:")
    print(final_state_dict.get('design', 'N/A'))
    print("\nCode:")
    print(final_state_dict.get('code', 'N/A'))
    print("\nTest Results:")
    print(final_state_dict.get('test_results', 'N/A'))
    print("\nReview Feedback:")
    print(final_state_dict.get('review_feedback', 'N/A'))
    print("\nStrategic Guidance:")
    print(final_state_dict.get('strategic_guidance', 'N/A'))
    print("-----------------------------")

    print("\n✅ Demonstration complete. Check the output above for generated deliverables.")

if __name__ == "__main__":
    asyncio.run(main())
