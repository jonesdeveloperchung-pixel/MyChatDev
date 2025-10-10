"""
Quick test script to verify system functionality.

This file exercises the `SimpleCooperativeLLM` workflow with a minimal
iteration count, ensuring that:

* the Ollama server is reachable and the requested model is available
* the workflow can run through its `run` method without raising an exception
* the final state contains the expected fields (iterations, requirements,
  design, code, deliverables)
"""

import asyncio

# Local imports – adjust if the package layout changes
from workflow.simple_workflow import SimpleCooperativeLLM
from config.settings import DEFAULT_CONFIG
from utils.logging_config import setup_logging


async def test_basic_functionality() -> bool:
    """
    Run a quick integration test of the Cooperative LLM workflow.

    Returns
    -------
    bool
        ``True`` if the test succeeded, ``False`` otherwise.
    """
    # Configure a logger for this test – INFO is enough to see progress
    logger = setup_logging("INFO")
    logger.info("Testing Cooperative LLM System")

    # Example prompt that the workflow will attempt to solve
    user_input = """
    Create a simple Python calculator that can:
    1. Perform basic arithmetic operations (add, subtract, multiply, divide)
    2. Handle user input validation
    3. Include error handling for division by zero
    4. Have a simple command-line interface
    """

    try:
        # Use the default config but limit iterations to keep the test fast
        config = DEFAULT_CONFIG
        config.max_iterations = 1  # One iteration is enough for a smoke‑test

        # Initialise the workflow – this loads the LLM manager and other
        # resources needed for the run.
        workflow = SimpleCooperativeLLM(config)
        logger.info("Workflow initialized successfully")

        # Verify that the LLM manager can reach the required model
        logger.info("Testing LLM Manager...")
        models_available = await workflow.llm_manager.check_model_availability("gemma3:4b")
        logger.info(f"Model gemma3:4b available: {models_available}")

        if models_available:
            # Run the full workflow once
            logger.info("Running full workflow...")
            final_state = await workflow.run(user_input)

            # Pretty‑print some metrics about the run
            logger.info("=== WORKFLOW RESULTS ===")
            logger.info(f"Iterations: {final_state.iteration_count}")
            logger.info(f"Requirements length: {len(final_state.requirements)} chars")
            logger.info(f"Design length: {len(final_state.design)} chars")
            logger.info(f"Code length: {len(final_state.code)} chars")

            print("\n🎉 SYSTEM TEST COMPLETED SUCCESSFULLY!")
            print(f"📊 Generated {len(final_state.deliverables)} deliverables")
            print(f"🔄 Completed {final_state.iteration_count} iterations")

            return True
        else:
            # Skip the full run if the model isn't available
            logger.warning("Required models not available - skipping full test")
            print("⚠️  Models not available - please ensure Ollama is running with required models")
            return False

    except Exception as e:
        # Catch any unexpected errors and log them
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")
        return False


# --------------------------------------------------------------------------- #
# Entry point for running the script directly (e.g. `python test_script.py`)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed – check the logs for details")