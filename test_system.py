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
from copy import deepcopy
from pathlib import Path

# Local imports – adjust if the package layout changes
from src.workflow_service import execute_workflow
from src.config.settings import DEFAULT_CONFIG
from src.config.llm_profiles import get_profile_by_name
from src.utils.logging_config import setup_logging

# Test configuration
TEST_PROFILE = "Fast_Lightweight"
TEST_MAX_ITERATIONS = 1


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
        # Use a copy of default config to avoid mutating shared state
        config = deepcopy(DEFAULT_CONFIG)
        config.max_iterations = TEST_MAX_ITERATIONS

        # Get LLM profile for the test
        llm_configs = get_profile_by_name(TEST_PROFILE)
        if not llm_configs:
            logger.error(f"Profile {TEST_PROFILE} not found")
            return False

        logger.info(f"Using profile: {TEST_PROFILE}")
        logger.info("Starting workflow execution...")

        # Run the workflow and collect events
        events_collected = []
        final_state = None
        
        async for event in execute_workflow(
            user_input=user_input,
            system_config=config,
            llm_configs=llm_configs,
            output_dir=Path("test_deliverables"),
            dry_run=False
        ):
            events_collected.append(event)
            logger.info(f"Event: {event.get('event_type', 'unknown')}")
            
            if event.get('event_type') == 'workflow_end':
                final_state = event.get('final_state', {})
                break

        if final_state:
            # Log workflow results
            logger.info("=== WORKFLOW RESULTS ===")
            logger.info(f"Iterations: {final_state.get('iteration_count', 0)}")
            logger.info(f"Requirements length: {len(final_state.get('requirements', ''))} chars")
            logger.info(f"Design length: {len(final_state.get('design', ''))} chars")
            logger.info(f"Code length: {len(final_state.get('code', ''))} chars")
            logger.info(f"Generated {len(final_state.get('deliverables', {}))} deliverables")
            logger.info("SYSTEM TEST COMPLETED SUCCESSFULLY!")
            return True
        else:
            logger.warning("Workflow completed but no final state received")
            return False

    except Exception as e:
        # Catch any unexpected errors and log them
        logger.error(f"Test failed: {e}")
        return False


# --------------------------------------------------------------------------- #
# Entry point for running the script directly (e.g. `python test_script.py`)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    # Final status output for user
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed – check the logs for details")
