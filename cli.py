#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Cooperative LLM System.

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
from workflow.simple_workflow import SimpleCooperativeLLM, WorkflowState
from config.settings import DEFAULT_CONFIG
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
5. Support dynamic configuration and modular drivers for Raspberry Pi hardware variants and protocols (e.g., BCM283x series, Pi 4 USB stack)
The RTOS must be bootable from the Raspberry Pi firmware (via `bootcode.bin` and `config.txt`), include a minimal Assembly bootloader to initialize the MMU and stack, and launch a Rust‑based kernel with C interop support. The system should be production‑ready, featuring onboarding‑friendly documentation, integration tests, and reproducible builds via cross‑compilation and QEMU emulation.
"""
# -------------------------------------------------------------------------------- #

# ---------- Helper: read prompt from file ----------
def _read_prompt_from_file(file_path: Path) -> str:
    """Read and return the entire contents of *file_path*."""
    try:
        content = file_path.read_text(encoding="utf-8")
        # ---- DEBUG --------------------------------------------------------------
        print(f"[DEBUG] Prompt read from '{file_path}'. Length = {len(content)}")
        # --------------------------------------------------------------------------- #
        return content
    except Exception as exc:
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
        if content:                     # skip empty sections
            file_path = timestamp_dir / filename   # <-- correct path
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

# ---------- Main ---------------------------------------------------------------- #
# NOTE: We now *accept* an explicit ``llm_configs`` dictionary.  This is the
# key to making the profile switch actually work.
async def main(user_input: str, llm_configs: dict) -> WorkflowState:
    """Main execution function."""
    # Setup logging (this will respect ``--debug`` later on)
    logger = setup_logging(DEFAULT_CONFIG.log_level)
    logger.info("=== COOPERATIVE LLM SYSTEM STARTUP ===")

    # ---- DEBUG --------------------------------------------------------------
    print("\n[DEBUG] User prompt starts with:")
    print(user_input[:200] + ("..." if len(user_input) > 200 else ""))
    print(f"[DEBUG] Selected profile: {list(llm_configs.keys())[0] if llm_configs else 'N/A'}")
    # Log the whole config mapping for manual inspection
    for role, cfg in llm_configs.items():
        print(f"[DEBUG]  Role '{role}': model={cfg.model_id}  temp={cfg.temperature}")
    # --------------------------------------------------------------------------- #

    try:
        # Initialise and run workflow
        #   * Pass the chosen llm_configs to the workflow
        workflow = SimpleCooperativeLLM(DEFAULT_CONFIG, llm_configs)
        logger.info(f"Starting workflow with input: {user_input[:100]}...")
        # Execute workflow
        final_state = await workflow.run(user_input)
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
        return final_state
    except Exception as exc:
        logger.error(f"Fatal error in main execution: {exc}")
        raise
# -------------------------------------------------------------------------------- #

# ---------- CLI entry point ----------------------------------------------------- #
def _build_arg_parser() -> argparse.ArgumentParser:
    """Return a fully‑configured ArgumentParser instance."""
    parser = argparse.ArgumentParser(
        description="Cooperative LLM workflow runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-U",
        "--user_prompt",
        type=Path,
        metavar="FILE",
        help=(
            "Path to a file containing the user prompt. "
            "If omitted, the built‑in default prompt is used."
        ),
    )
    parser.add_argument(
        "-P",
        "--profile",
        type=str,
        choices=AVAILABLE_LLMS_BY_PROFILE.keys(),
        default="optimized",
        help=(
            "Select which LLM profile to use.  Each profile bundles a set of "
            "model IDs, temperatures, etc."
        ),
    )
    # ---- DEBUG OPTION ----------------------------------------------
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Turn on extra diagnostic output (prints, timestamps, etc.)",
    )
    # ---------------------------------------------------------------
    return parser

if __name__ == "__main__":
    parser = _build_arg_parser()
    args = parser.parse_args()

    # ---- DEBUG --------------------------------------------------------------
    print("\n[DEBUG] CLI parsed arguments:")
    print(f"  user_prompt  = {args.user_prompt}")
    print(f"  profile      = {args.profile}")
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
    print(f"[DEBUG] Using profile '{args.profile}'.  Number of roles = {len(llm_configs)}")
    # --------------------------------------------------------------------------- #

    # Run the event loop
    asyncio.run(main(user_input, llm_configs))