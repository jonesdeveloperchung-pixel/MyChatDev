"""Main entry point for the Cooperative LLM System."""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from workflow.simple_workflow import SimpleCooperativeLLM
from config.settings import DEFAULT_CONFIG
from utils.logging_config import setup_logging


async def save_deliverables(state, output_dir: Path):
    """Save all deliverables to files."""
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save individual deliverables
    deliverable_files = {
        "requirements_specification.md": state.requirements,
        "system_design.md": state.design,
        "source_code.py": state.code,
        "test_results.md": state.test_results,
        "review_feedback.md": state.review_feedback
    }
    
    for filename, content in deliverable_files.items():
        if content:
            file_path = output_dir / f"{timestamp}_{filename}"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    # Save complete state as JSON
    state_data = {
        "user_input": state.user_input,
        "deliverables": state.deliverables,
        "quality_evaluations": state.quality_evaluations,
        "iteration_count": state.iteration_count,
        "timestamp": timestamp
    }
    
    state_file = output_dir / f"{timestamp}_complete_state.json"
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state_data, f, indent=2, ensure_ascii=False)
    
    return output_dir, timestamp


async def main():
    """Main execution function."""
    
    # Setup logging
    logger = setup_logging(DEFAULT_CONFIG.log_level)
    logger.info("=== COOPERATIVE LLM SYSTEM STARTUP ===")
    
    # Example user input - replace with actual input
    user_input = """
        Design and implement a bootable, modular Real-Time Operating System (RTOS) for Raspberry Pi (ARMv7/ARMv8) using Rust, Assembly, and C, with the following capabilities:

        1. Detect and extract metadata from connected peripherals (e.g., USB, GPIO, I2C, SPI) to simulate dynamic hardware discovery and initialization
        2. Enforce system-level rate limiting and access control policies for I/O operations and task scheduling, configurable via external TOML/JSON files
        3. Persist structured telemetry and system logs using an embedded, SQLite-compatible storage layer optimized for SD card wear-leveling
        4. Provide robust error handling and kernel-level logging across all subsystems, including bootloader, scheduler, and device drivers
        5. Support dynamic configuration and modular drivers for Raspberry Pi hardware variants and protocols (e.g., BCM283x series, Pi 4 USB stack)

        The RTOS must be bootable from the Raspberry Pi firmware (via `bootcode.bin` and `config.txt`), include a minimal Assembly bootloader to initialize the MMU and stack, and launch a Rust-based kernel with C interop support. The system should be production-ready, featuring onboarding-friendly documentation, integration tests, and reproducible builds via cross-compilation and QEMU emulation.
        """
    
    try:
        # Initialize and run workflow
        workflow = SimpleCooperativeLLM(DEFAULT_CONFIG)
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
        
        print("\n" + "="*60)
        print("🎉 COOPERATIVE LLM WORKFLOW COMPLETED!")
        print(f"📁 Deliverables saved to: {saved_dir}")
        print(f"🔄 Iterations: {final_state.iteration_count}")
        print("="*60)
        
        return final_state
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())