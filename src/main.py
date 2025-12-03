"""Main entry point for the Cooperative LLM System.

Author: Jones Chung
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import time # Import time for measuring execution time

# Removed GraphWorkflow import as it's now encapsulated
from config.settings import DEFAULT_CONFIG, SystemConfig
from config.llm_profiles import AVAILABLE_LLMS_BY_PROFILE # Import profiles
from utils.logging_config import setup_logging
from .workflow_service import execute_workflow, save_deliverables # Import execute_workflow and save_deliverables from service


# Removed save_deliverables helper function as it's now in src/workflow_service.py
# async def save_deliverables(state, output_dir: Path, timestamp: str):
#     """Save all deliverables to files."""
#     output_dir.mkdir(parents=True, exist_ok=True)

#     # Create a sub‑folder named with the current timestamp
#     # (e.g. 20251004-154609).
#     timestamp_dir = output_dir / timestamp
#     timestamp_dir.mkdir(parents=True, exist_ok=True)

#     # Save individual deliverables
#     deliverable_files = {
#         "requirements_specification.md": state.requirements,
#         "system_design.md": state.design,
#         "source_code.py": state.code,
#         "test_results.md": state.test_results,
#         "review_feedback.md": state.review_feedback,
#         "strategic_guidance.md": state.strategic_guidance, # Include strategic guidance
#     }

#     for filename, content in deliverable_files.items():
#         if content:
#             file_path = timestamp_dir / filename
#             with open(file_path, "w", encoding="utf-8") as f:
#                 f.write(content)

#     # Save complete state as JSON
#     state_data = {
#         "user_input": state.user_input,
#         "deliverables": state.deliverables,
#         "quality_evaluations": state.quality_evaluations,
#         "iteration_count": state.iteration_count,
#         "should_halt": state.should_halt, # Include should_halt
#         "timestamp": timestamp,
#     }

#     state_file = timestamp_dir / f"{timestamp}_complete_state.json"
#     with open(state_file, "w", encoding="utf-8") as f:
#         json.dump(state_data, f, indent=2, ensure_ascii=False)

#     return timestamp_dir, timestamp


async def main():
    """Main execution function."""

    # Setup logging
    logger = setup_logging(DEFAULT_CONFIG.log_level)
    logger.info("=== COOPERATIVE LLM SYSTEM STARTUP ===")

    # Define multiple test cases
    test_cases = [
        """Create a Python function that calculates the factorial of a number. Include unit tests for positive, zero, and negative inputs.""",
        """Implement a simple C program that reverses a string. Include a Makefile for compilation and testing.""",
        # Add more test cases here
    ]

    all_results = []

    # Define the default profile to use for main.py test cases
    default_profile = 'Compliance_Focused' # Or 'medium_reasoning', 'low_reasoning'
    llm_configs = AVAILABLE_LLMS_BY_PROFILE[default_profile]

    for i, user_input in enumerate(test_cases):
        logger.info(f"--- Running Test Case {i+1}/{len(test_cases)} ---")
        start_time = time.time() # This time tracking will be overwritten by execute_workflow's internal timing

        try:
            # Create a custom SystemConfig for this test run (can be customized per test case)
            custom_config = SystemConfig(
                ollama_host=DEFAULT_CONFIG.ollama_host,
                max_iterations=DEFAULT_CONFIG.max_iterations,
                quality_threshold=DEFAULT_CONFIG.quality_threshold,
                change_threshold=DEFAULT_CONFIG.change_threshold,
                log_level=DEFAULT_CONFIG.log_level,
                enable_sandbox=DEFAULT_CONFIG.enable_sandbox,
                enable_compression=DEFAULT_CONFIG.enable_compression,
                compression_threshold=DEFAULT_CONFIG.compression_threshold,
                compression_strategy=DEFAULT_CONFIG.compression_strategy,
                max_compression_ratio=DEFAULT_CONFIG.max_compression_ratio,
                compression_chunk_size=DEFAULT_CONFIG.compression_chunk_size,
                stagnation_iterations=DEFAULT_CONFIG.stagnation_iterations,
                enable_human_approval=DEFAULT_CONFIG.enable_human_approval,
            )
            logger.debug(f"Custom config for test case {i+1}: {custom_config}")

            # Execute workflow using the service function
            final_state_dict = await execute_workflow(
                user_input=user_input,
                system_config=custom_config,
                llm_configs=llm_configs,
                dry_run=False # main.py runs actual tests
            )

            # Collect results from the returned dictionary
            result = {
                "test_case_id": i + 1,
                "user_input": user_input,
                "iterations": final_state_dict.get('iteration_count', 0),
                "halted_successfully": final_state_dict.get('should_halt', False),
                "final_quality_score": final_state_dict.get('final_quality_score', 0),
                "time_to_completion": final_state_dict.get('time_to_completion', 0),
                "deliverables_path": final_state_dict.get('deliverables_path', 'N/A'),
                "status": final_state_dict.get('status', 'completed')
            }
            all_results.append(result)

            logger.info(f"Test Case {i+1} Summary:")
            logger.info(f"  Iterations: {result['iterations']}")
            logger.info(f"  Halted Successfully: {result['halted_successfully']}")
            logger.info(f"  Final Quality Score: {result['final_quality_score']:.2f}")
            logger.info(f"  Time to Completion: {result['time_to_completion']:.2f} seconds")
            logger.info(f"  Deliverables saved to: {result['deliverables_path']}")

        except Exception as e:
            logger.error(f"Error running test case {i+1}: {e}")
            all_results.append({
                "test_case_id": i + 1,
                "user_input": user_input,
                "error": str(e),
                "time_to_completion": time.time() - start_time, # Fallback if execute_workflow didn't return time
                "status": "error"
            })
        logger.info(f"--- Finished Test Case {i+1} ---")
        logger.info("-" * 80)


    logger.info("=== ALL TEST CASES COMPLETED ===")
    logger.info("--- Overall Performance Summary ---")
    for res in all_results:
        if res.get("status") == "error":
            logger.info(f"Test Case {res['test_case_id']}: ERROR - {res['error']} (Time: {res['time_to_completion']:.2f}s)")
        else:
            logger.info(f"Test Case {res['test_case_id']}: Iterations={res['iterations']}, Halted={res['halted_successfully']}, Quality={res['final_quality_score']:.2f}, Time={res['time_to_completion']:.2f}s")

    # Optionally save all_results to a JSON file
    results_file = Path("deliverables") / f"performance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    logger.info(f"Performance summary saved to {results_file}")

    print("\n" + "=" * 60)
    print("🎉 ALL COOPERATIVE LLM WORKFLOW TEST CASES COMPLETED!")
    print(f"📊 Performance summary saved to: {results_file}")
    print("=" * 60)

    return all_results


if __name__ == "__main__":
    asyncio.run(main())
