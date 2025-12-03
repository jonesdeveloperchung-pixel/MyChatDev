import asyncio
import json
from pathlib import Path
from datetime import datetime
import time
from typing import Dict, Any, Tuple, AsyncGenerator

from .workflow.graph_workflow import GraphWorkflow
from .config.settings import SystemConfig, DEFAULT_CONFIG, LLMConfig
from .utils.logging_config import setup_logging
from .database import initialize_db, insert_workflow_run, update_workflow_run

# A simple in-memory store for active workflows for basic management
# In a production system, this would be a more robust persistent store
active_workflows: Dict[str, Any] = {}


async def save_deliverables(state: Dict[str, Any], output_dir: Path, timestamp: str) -> Tuple[Path, str]:
    """Save all deliverables to files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp_dir = output_dir / timestamp
    timestamp_dir.mkdir(parents=True, exist_ok=True)

    # Access state attributes safely from the dictionary
    deliverable_files = {
        "requirements_specification.md": state.get("requirements", None),
        "system_design.md": state.get("design", None),
        "source_code.py": state.get("code", None),
        "test_results.md": state.get("test_results", None),
        "review_feedback.md": state.get("review_feedback", None),
        "strategic_guidance.md": state.get("strategic_guidance", None),
    }

    for filename, content in deliverable_files.items():
        if content:
            file_path = timestamp_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

    state_data = {
        "user_input": state.get("user_input", None),
        "deliverables": state.get("deliverables", None),
        "quality_evaluations": state.get("quality_evaluations", None),
        "iteration_count": state.get("iteration_count", 0),
        "should_halt": state.get("should_halt", False),
        "timestamp": timestamp,
    }

    state_file = timestamp_dir / f"{timestamp}_complete_state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2, ensure_ascii=False)

    return timestamp_dir, timestamp


async def execute_workflow(
    user_input: str,
    system_config: SystemConfig,
    llm_configs: Dict[str, LLMConfig],
    output_dir: Path = Path("deliverables"),
    dry_run: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes the core cooperative LLM workflow as an async generator,
    yielding structured events for real-time updates.

    Args:
        user_input (str): The user's prompt for the workflow.
        system_config (SystemConfig): Configuration for the system.
        llm_configs (Dict[str, LLMConfig]): LLM configurations for each role.
        output_dir (Path): Directory to save deliverables.
        dry_run (bool): If True, simulate the workflow without execution.

    Yields:
        Dict[str, Any]: Structured event objects representing workflow progress,
                        logs, node outputs, and final status.
    """
    logger = setup_logging(system_config.log_level) # Use system_config.log_level

    # Initialize the database schema
    initialize_db(system_config.database_url)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Insert initial workflow run record
    insert_workflow_run(
        run_id=run_id,
        status="running",
        start_time=str(datetime.now()),
        user_prompt=user_input,
        config_used=system_config.model_dump_json(),
        database_url=system_config.database_url
    )
    
    yield {"event_type": "workflow_start", "run_id": run_id, "timestamp": str(datetime.now()), "message": "Starting cooperative LLM workflow."}
    logger.info("=== COOPERATIVE LLM WORKFLOW EXECUTION ===")
    logger.debug(f"Run ID: {run_id}")
    logger.debug(f"User Input (first 100 chars): {user_input[:100]}...")
    logger.debug(f"System Config: {system_config.model_dump_json(indent=2)}")
    logger.debug(f"LLM Configs (first role): {list(llm_configs.keys())[0] if llm_configs else 'N/A'}")
    if llm_configs:
        for role, cfg in llm_configs.items():
            logger.debug(f"  Role '{role}': model={cfg.model_id}  temp={cfg.temperature}")

    if dry_run:
        yield {"event_type": "log", "level": "INFO", "message": "Dry run enabled. Simulating workflow."}
        yield {"event_type": "dry_run_summary", "payload": {
            "user_input": user_input,
            "system_config": system_config.model_dump(),
            "llm_configs": {k: v.model_dump() for k, v in llm_configs.items()},
            "message": "Workflow simulation complete."
        }}
        yield {"event_type": "workflow_end", "run_id": run_id, "timestamp": str(datetime.now()), "status": "dry_run_completed", "message": "Dry run complete."}
        return # Exit for dry run

    start_time = time.time()
    final_state: Dict[str, Any] = {} # Initialize final_state as a dict
    
    try:
        workflow = GraphWorkflow(system_config, llm_configs)
        
        initial_state = {
            "user_input": user_input,
            "iteration_count": 0,
            "should_halt": False,
            "requirements": "",
            "design": "",
            "code": "",
            "test_results": "",
            "review_feedback": "",
            "deliverables": {}, # Initialize empty
            "quality_evaluations": [],
            "strategic_guidance": "",
            "human_approval": False, # Initialize human_approval
        }
        
        recursion_limit = system_config.max_iterations * 10
        yield {"event_type": "log", "level": "DEBUG", "message": f"Setting graph recursion limit to: {recursion_limit}"}

        # Use astream to get intermediate updates
        async for state_update in workflow.graph.astream(initial_state, config={"recursion_limit": recursion_limit}):
            for node_name, node_output in state_update.items():
                if node_name == "__end__": # This is the final state after a step
                    final_state = node_output
                    # Yield a summary of the node output or full state
                    yield {"event_type": "state_update", "payload": final_state, "timestamp": str(datetime.now())}
                else: # Intermediate node execution
                    yield {"event_type": "node_execution", "node": node_name, "output": node_output, "timestamp": str(datetime.now())}
            
            # Optionally, you can add more granular event types here, e.g., for logs within nodes
            # This would require modifying GraphWorkflow nodes to yield logs.
        
        # After the streaming finishes, the last state yielded by __end__ is the final state
        # LangGraph's astream typically yields an update for each node, and then a final "__end__" state update.
        # We need to make sure we capture the true final state for saving deliverables.
        # If the last `state_update` was the final state, `final_state` should already be populated.
        
        if not final_state: # Fallback if for some reason __end__ wasn't explicitly captured
            # This case might happen if the graph only has one node and it ends there
            # Or if astream's behavior changes. It's safer to ensure final_state is updated.
            # LangGraph astream's last yield *should* contain the full final state.
            pass # final_state should be populated by the __end__ node_name above
            
        # Ensure 'deliverables' is populated in the final state for saving
        if final_state and 'deliverables' not in final_state:
            final_state['deliverables'] = {
                'requirements': final_state.get('requirements', ''),
                'design': final_state.get('design', ''),
                'code': final_state.get('code', ''),
                'test_results': final_state.get('test_results', ''),
                'review_feedback': final_state.get('review_feedback', ''),
                'strategic_guidance': final_state.get('strategic_guidance', ''),
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_dir, _ = await save_deliverables(final_state, output_dir, timestamp) # save using final_state

        end_time = time.time()
        time_to_completion = end_time - start_time

        final_quality = 0
        if final_state.get('quality_evaluations'):
            final_quality = final_state['quality_evaluations'][-1].get("overall_quality_score", 0)
        
        final_state['final_quality_score'] = final_quality
        final_state['time_to_completion'] = time_to_completion
        final_state['deliverables_path'] = str(saved_dir)
        final_state['status'] = 'completed'
        final_state['run_id'] = run_id

        # Update the workflow run record in the database
        update_workflow_run(
            run_id=run_id,
            status="completed",
            end_time=str(datetime.now()),
            review_feedback=final_state.get('review_feedback', None),
            deliverables_path=str(saved_dir),
            database_url=system_config.database_url
        )

        yield {"event_type": "workflow_end", "run_id": run_id, "timestamp": str(datetime.now()), "status": "completed", "final_state": final_state, "message": "Workflow completed successfully."}
        logger.info(f"Workflow {run_id} completed. Deliverables saved to: {saved_dir}")

    except Exception as exc:
        logger.fatal(f"Fatal error during workflow execution for run {run_id}: {exc}")
        error_state = {
            "run_id": run_id,
            "status": "error",
            "error_message": str(exc),
            "timestamp": str(datetime.now())
        }
        yield {"event_type": "workflow_error", "run_id": run_id, "timestamp": str(datetime.now()), "status": "error", "error_details": str(exc)}
        # It's important to still save the partial state or error log if possible
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_dir, _ = await save_deliverables(final_state, output_dir, timestamp) # Attempt to save partial deliverables
            error_state['deliverables_path'] = str(saved_dir)

            # Update the workflow run record in the database with error status
            update_workflow_run(
                run_id=run_id,
                status="error",
                end_time=str(datetime.now()),
                review_feedback=f"Workflow terminated with error: {exc}",
                deliverables_path=str(saved_dir),
                database_url=system_config.database_url
            )
        except Exception as save_exc:
            logger.error(f"Error saving partial deliverables for run {run_id} after workflow error: {save_exc}")
        finally:
            active_workflows.pop(run_id, None) # Clean up active workflow entry

