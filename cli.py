#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Cooperative LLM System.

Author: Jones Chung

Improvements added:
    * -U/--user_prompt: read the prompt from a file (unchanged).
    * -P/--profile      : choose a model profile from the mapping
                          (default = “optimized”).
    * --debug           : turn on *debug*‑level logging and a few
                          ``print``‑based diagnostics.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# ---------- Import everything that the original script needs ----------
from workflow.graph_workflow import GraphWorkflow, GraphState
from config.settings import DEFAULT_CONFIG, SystemConfig
from utils.logging_config import setup_logging
from config.llm_profiles import AVAILABLE_LLMS_BY_PROFILE

# ------------------------------------------------- END IMPORTS ------------------------------------------------ #


# ---------- Default prompt (kept identical to the original hard‑coded string) ----------
DEFAULT_USER_PROMPT: str = """
Design and implement a bootable, modular Real‑Time Operating System (RTOS) for Raspberry Pi (ARMv7/ARMv8) using Rust, Assembly, and C, with the following capabilities:
1. Detect and extract metadata from connected peripherals (e.g., USB, GPIO, I2C, SPI) to simulate dynamic hardware discovery and initialization
2. Enforce system‑level rate limiting and access control policies for I/O operations and task scheduling, configurable via external TOML/JSON files
3. Persist structured telemetry and system logs using an embedded, SQLite‑compatible storage layer optimized for SD card wear‑leveling
4. Provide robust error handling and kernel‑level logging across all subsystems, including bootloader, scheduler, and device drivers
5. Support dynamic configuration and modular drivers for Raspberry Pi hardware variants and protocols (e.g., BCM283x series, Pi 4 USB stack)
The RTOS must be bootable from the Raspberry Pi firmware (via `bootcode.bin` and `config.txt`), include a minimal Assembly bootloader to initialize the MMU and stack, and launch a Rust‑based kernel with C interop support. The system should be production‑ready, featuring onboarding‑friendly documentation, integration tests, and reproducible builds via cross‑compilation and QEMU emulation.
"""
# -------------------------------------------------------------------------------- #


# ---------- Helper: read prompt from file ----------
def _read_prompt_from_file(file_path: Path) -> str:
    """Read and return the entire contents of *file_path*. """
    try:
        content = file_path.read_text(encoding="utf-8")
        # ---- DEBUG --------------------------------------------------------------
        if args.debug:
            logger.debug(f"Prompt read from '{file_path}'. Length = {len(content)}")
        # --------------------------------------------------------------------------- #
        return content
    except Exception as exc:
        logger.fatal(f"Failed to read prompt file '{file_path}': {exc}")
        raise RuntimeError(f"Failed to read prompt file '{file_path}': {exc}") from exc


# -------------------------------------------------------------------------------- #


# ---------- Helper: save deliverables (unchanged but with comments) ----------
async def save_deliverables(state, output_dir: Path):
    """
    Save all deliverables to files.
    Parameters
    ----------
    state: WorkflowState
        The final state returned by the workflow.
    output_dir: Path
        The base directory where deliverables will be stored.
    """
    # 1. Make sure the base folder exists.
    output_dir.mkdir(parents=True, exist_ok=True)
    # 2. Create a sub‑folder named with the current timestamp
    #    (e.g. 20251004-154609).
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    timestamp_dir = output_dir / timestamp
    timestamp_dir.mkdir(parents=True, exist_ok=True)
    # 3. Map state attributes to file names.
    deliverable_files = {
        "requirements_specification.md": state.requirements,
        "system_design.md": state.design,
        "source_code.md": state.code,
        "test_results.md": state.test_results,
        "review_feedback.md": state.review_feedback,
    }
    # 4. Write each deliverable.
    for filename, content in deliverable_files.items():
        if content:  # skip empty sections
            file_path = timestamp_dir / filename  # <-- correct path
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
    # 5. Dump the whole state to a JSON file for later inspection.
    state_data = {
        "user_input": state.user_input,
        "deliverables": state.deliverables,
        "quality_evaluations": state.quality_evaluations,
        "iteration_count": state.iteration_count,
        "timestamp": timestamp,
    }
    state_file = timestamp_dir / f"{timestamp}_complete_state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2, ensure_ascii=False)
    # Return the directory that now contains the files and the timestamp used.
    return timestamp_dir, timestamp


# -------------------------------------------------------------------------------- #


# ---------- Helper: Normalize Ollama URL ----------
def _normalize_ollama_url(url_string: str) -> str:
    """
    Normalizes an Ollama URL string by ensuring it has a scheme (http://)
    and a default port (11434) if not specified.
    """
    # Ensure scheme is present
    if not url_string.startswith("http://") and not url_string.startswith("https://"):
        url_string = f"http://{url_string}"

    # Check if a port is specified. If not, append the default Ollama port.
    # This is a simple check and might not cover all edge cases, but should work for IP:Port and IP.
    # We look for a colon AFTER the scheme part.
    if ":" not in url_string.split("//", 1)[-1]:
        url_string = f"{url_string}:11434" # Default Ollama port

    return url_string


# -------------------------------------------------------------------------------- #


# ---------- Main ---------------------------------------------------------------- #
# NOTE: We now *accept* an explicit ``llm_configs`` dictionary.  This is the
# key to making the profile switch actually work.
async def main(user_input: str, llm_configs: dict, system_config: SystemConfig) -> GraphState:
    """Main execution function."""
    # Setup logging (this will respect ``--debug`` later on)
    logger = setup_logging(system_config.log_level) # Use system_config.log_level
    logger.info("=== COOPERATIVE LLM SYSTEM STARTUP ===")

    # ---- DEBUG --------------------------------------------------------------
    if args.debug:
        logger.debug("\nUser prompt starts with:")
        logger.debug(user_input[:200] + ("..." if len(user_input) > 200 else ""))
        logger.debug(
            f"Selected profile: {list(llm_configs.keys())[0] if llm_configs else 'N/A'}"
        )
        # Log the whole config mapping for manual inspection
        for role, cfg in llm_configs.items():
            logger.debug(f"  Role '{role}': model={cfg.model_id}  temp={cfg.temperature}")
    # --------------------------------------------------------------------------- #

    try:
        # Initialise and run workflow
        #   * Pass the chosen llm_configs to the workflow
        workflow = GraphWorkflow(system_config, llm_configs) # Pass system_config
        logger.info(f"Starting workflow with input: {user_input[:100]}...")
        # Execute workflow
        final_state_dict = await workflow.run(user_input)

        # HACK: Convert dict to a temporary object to maintain compatibility with save_deliverables
        class TempState:
            def __init__(self, **entries):
                self.__dict__.update(entries)

        final_state = TempState(**final_state_dict)

        # Save deliverables
        output_dir = Path("deliverables")
        saved_dir, timestamp = await save_deliverables(final_state, output_dir)
        # Print summary
        logger.info("=== WORKFLOW SUMMARY ===")
        logger.info(f"Iterations completed: {final_state.iteration_count}")
        logger.info(f"Quality evaluations: {len(final_state.quality_evaluations)}")
        logger.info(f"Deliverables saved to: {saved_dir}")
        # Print final quality score
        if final_state.quality_evaluations:
            final_quality = final_state.quality_evaluations[-1].get("quality_score", 0)
            logger.info(f"Final quality score: {final_quality:.2f}")
        print("\n" + "=" * 60)
        print("🎉 COOPERATIVE LLM WORKFLOW COMPLETED!")
        print(f"📁 Deliverables saved to: {saved_dir}")
        print(f"🔄 Iterations: {final_state.iteration_count}")
        print("=" * 60)
        return final_state_dict
    except Exception as exc:
        logger.fatal(f"Fatal error in main execution: {exc}")
        raise


# -------------------------------------------------------------------------------- #


# ---------- CLI entry point ----------------------------------------------------- #
def _build_arg_parser() -> argparse.ArgumentParser:
    """Return a fully‑configured ArgumentParser instance."""
    parser = argparse.ArgumentParser(
        description="Run a Cooperative LLM workflow to autonomously develop software. This tool orchestrates multiple LLM agents (Product Manager, Architect, Programmer, Tester, etc.) to iteratively refine requirements, design, code, and tests, aiming for high-quality software deliverables.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-U",
        "--user_prompt",
        type=Path,
        metavar="FILE",
        help=(
            "Path to a file containing the initial user prompt. "
            "If omitted, a built-in default prompt is used."
        ),
    )
    parser.add_argument(
        "-P",
        "--profile",
        type=str,
        choices=AVAILABLE_LLMS_BY_PROFILE.keys(),
        default="High_Reasoning",
        help=(
            "Select which LLM profile to use.  Each profile bundles a set of "
            "model IDs, temperatures, etc."
        ),
    )
    # ---- DEBUG OPTION ----------------------------------------------
    parser.add_argument(
        "-D",
        "--debug",
        action="store_true",
        help="Turn on extra diagnostic output (prints, timestamps, etc.)",
    )
    # ---- OLLAMA HOST OPTION ----------------------------------------
    parser.add_argument(
        "-O",
        "--ollama_url",
        type=str,
        default=DEFAULT_CONFIG.ollama_host,
        help="URL of the Ollama host.",
    )
    # ---------------------------------------------------------------
    
    # ---- SYSTEM CONFIGURATION OPTIONS ------------------------------
    parser.add_argument(
        "-S",
        "--enable_sandbox",
        type=lambda x: x.lower() == 'true', # Convert string to boolean
        default=DEFAULT_CONFIG.enable_sandbox,
        help="Enable or disable the sandboxed development environment.",
    )
    parser.add_argument(
        "-I",
        "--max_iterations",
        type=int,
        default=DEFAULT_CONFIG.max_iterations,
        help="Maximum number of iterations for the workflow.",
    )
    parser.add_argument(
        "-Q",
        "--quality_threshold",
        type=float,
        default=DEFAULT_CONFIG.quality_threshold,
        help="Quality score threshold for the Quality Gate to halt.",
    )
    parser.add_argument(
        "-C",
        "--change_threshold",
        type=float,
        default=DEFAULT_CONFIG.change_threshold,
        help="Change magnitude threshold for the Quality Gate to halt (stagnation).",
    )
    parser.add_argument(
        "-T",
        "--stagnation_iterations",
        type=int,
        default=DEFAULT_CONFIG.stagnation_iterations,
        help="Number of iterations to check for stagnation before triggering reflection.",
    )
    parser.add_argument(
        "-A",
        "--enable_human_approval",
        type=lambda x: x.lower() == 'true', # Convert string to boolean
        default=DEFAULT_CONFIG.enable_human_approval,
        help="Enable or disable the optional human approval step.",
    )
    # --------------------------------------------------------------- 
    return parser

if __name__ == "__main__":
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Setup logging early to capture all debug messages
    # Determine log_level based on --debug flag, but use a default config for initial setup
    # A more refined SystemConfig will be created later with all parsed arguments
    initial_log_level = "DEBUG" if args.debug else DEFAULT_CONFIG.log_level
    logger = setup_logging(initial_log_level)

    # ---- DEBUG --------------------------------------------------------------
    if args.debug:
        logger.debug("\nCLI parsed arguments:")
        logger.debug(f"  user_prompt  = {args.user_prompt}")
        logger.debug(f"  profile      = {args.profile}")
        logger.debug(f"  ollama_url   = {args.ollama_url}")
        logger.debug(f"  enable_sandbox = {args.enable_sandbox}")
        logger.debug(f"  max_iterations = {args.max_iterations}")
        logger.debug(f"  quality_threshold = {args.quality_threshold}")
        logger.debug(f"  change_threshold = {args.change_threshold}")
        logger.debug(f"  stagnation_iterations = {args.stagnation_iterations}")
        logger.debug(f"  enable_human_approval = {args.enable_human_approval}")
    # --------------------------------------------------------------------------- #

    # Resolve the user prompt
    if args.user_prompt:
        user_input = _read_prompt_from_file(args.user_prompt)
    else:
        user_input = DEFAULT_USER_PROMPT

    # Pull the chosen mapping out of the global table
    llm_configs = AVAILABLE_LLMS_BY_PROFILE[args.profile]
    AVAILABLE_LLMS = llm_configs  # <-- make it globally visible
    # ---- DEBUG --------------------------------------------------------------
    if args.debug:
        logger.debug(
            f"Using profile '{args.profile}'.  Number of roles = {len(llm_configs)}"
        )
    # --------------------------------------------------------------------------- #

    # Create a custom SystemConfig based on CLI arguments
    custom_config = SystemConfig(
        ollama_host=_normalize_ollama_url(args.ollama_url), # Use parsed URL and normalize it
        max_iterations=args.max_iterations,
        quality_threshold=args.quality_threshold,
        change_threshold=args.change_threshold,
        log_level="DEBUG" if args.debug else DEFAULT_CONFIG.log_level, # Set log_level based on --debug flag
        enable_sandbox=args.enable_sandbox,
        enable_compression=DEFAULT_CONFIG.enable_compression, # Keep default for now
        compression_threshold=DEFAULT_CONFIG.compression_threshold, # Keep default for now
        compression_strategy=DEFAULT_CONFIG.compression_strategy, # Keep default for now
        max_compression_ratio=DEFAULT_CONFIG.max_compression_ratio, # Keep default for now
        compression_chunk_size=DEFAULT_CONFIG.compression_chunk_size, # Keep default for now
        stagnation_iterations=args.stagnation_iterations,
        enable_human_approval=args.enable_human_approval,
    )

    # Run the event loop
    asyncio.run(main(user_input, llm_configs, custom_config))