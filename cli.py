#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Cooperative LLM System.

Author: Jones Chung

Improvements added:
    * -U/--user_prompt: read the prompt from a file (unchanged).
    * -P/--profile      : choose a model profile from the mapping
                          (default = "optimized").
    * --debug           : turn on '*debug*‑level' logging and a few
                          ``print``‑based diagnostics.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import yaml
import re # For URL validation
import os # For opening editor
import platform # For system info

from typing import Dict

# ---------- Import everything that the original script needs ----------
from workflow.graph_workflow import GraphWorkflow, GraphState
from config.settings import DEFAULT_CONFIG, SystemConfig, LLMConfig
from utils.logging_config import setup_logging
from config.llm_profiles import AVAILABLE_LLMS_BY_PROFILE

# ------------------------------------------------- END IMPORTS ------------------------------------------------ #


# ---------- Default prompt (kept identical to the original hard‑coded string) ----------
DEFAULT_USER_PROMPT: str = """
Design and implement a bootable, modular Real‑Time Operating System (RTOS) for
Raspberry Pi (ARMv7/ARMv8) using Rust, Assembly, and C, with the following
capabilities:
1. Detect and extract metadata from connected peripherals (e.g., USB, GPIO, I2C,
   SPI) to simulate dynamic hardware discovery and initialization
2. Enforce system‑level rate limiting and access control policies for I/O
   operations and task scheduling, configurable via external TOML/JSON files
3. Persist structured telemetry and system logs using an embedded,
   SQLite‑compatible storage layer optimized for SD card wear‑leveling
4. Provide robust error handling and kernel‑level logging across all
   subsystems, including bootloader, scheduler, and device drivers
5. Support dynamic configuration and modular drivers for Raspberry Pi hardware
   variants and protocols (e.g., BCM283x series, Pi 4 USB stack)
The RTOS must be bootable from the Raspberry Pi firmware (via `bootcode.bin`
and `config.txt`), include a minimal Assembly bootloader to initialize the MMU
and stack, and launch a Rust‑based kernel with C interop support. The system
should be production‑ready, featuring onboarding‑friendly documentation,
integration tests, and reproducible builds via cross‑compilation and QEMU
emulation.
"""
# -------------------------------------------------------------------------------- #


# ---------- Helper: read prompt from file ----------
def _read_prompt_from_file(file_path: Path) -> str:
    """Read and return the entire contents of *file_path*. """
    if not file_path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    try:
        content = file_path.read_text(encoding="utf-8")
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
    timestamp_dir = output_dir / timestamp  # <-- correct path
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
    # Basic URL validation regex (simplified)
    url_pattern = re.compile(r"^https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}(?::\d{1,5})?(?:/.*)?$")
    if not url_pattern.match(url_string):
        raise ValueError(f"Invalid URL format: {url_string}")

    # Ensure scheme is present
    if not url_string.startswith("http://") and not url_string.startswith("https://"):
        url_string = f"http://{url_string}"

    # Check if a port is specified. If not, append the default Ollama port.
    # This is a simple check and might not cover all edge cases, but should work for IP:Port and IP.
    # We look for a colon AFTER the scheme part.
    if ":" not in url_string.split("//", 1)[-1]:
        url_string = f"{url_string}:11434"  # Default Ollama port

    return url_string


# -------------------------------------------------------------------------------- #


def _load_profile_from_file(file_path: Path) -> Dict[str, LLMConfig]:
    """
    Loads an LLM profile from a specified YAML file.
    The file is expected to define a dictionary where keys are role names
    and values are dictionaries representing LLMConfig parameters.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Profile file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_configs = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Invalid YAML format in profile file '{file_path}'.") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to read profile file '{file_path}'.") from exc

    if not isinstance(raw_configs, dict):
        raise TypeError(
            f"Profile file '{file_path}' must contain a dictionary at its root."
        )

    loaded_configs: Dict[str, LLMConfig] = {}
    for role, config_data in raw_configs.items():
        if not isinstance(config_data, dict):
            raise TypeError(
                f"Configuration for role '{role}' in '{file_path}' must be a dictionary."
            )
        try:
            # Ensure name and role are present, or default them
            config_data.setdefault('name', role.replace('_', ' ').title())
            config_data.setdefault('role', role)
            loaded_configs[role] = LLMConfig(**config_data)
        except Exception as exc:
            raise ValueError(
                f"Invalid LLMConfig data for role '{role}' in '{file_path}'. "
                f"Details: {exc}"
            ) from exc
    
    return loaded_configs


# -------------------------------------------------------------------------------- #


# ---------- Run Command Function (formerly main) -------------------------------- #
async def run_command(args: argparse.Namespace) -> GraphState:
    """Executes the cooperative LLM workflow based on provided arguments."""
    
    # Setup logging
    log_level = args.log_level.upper() if args.log_level else DEFAULT_CONFIG.log_level
    logger = setup_logging(log_level)
    logger.info("=== COOPERATIVE LLM SYSTEM STARTUP ===")

    # --- Validation ---
    # User Prompt Source
    if args.user_prompt_file and args.user_prompt_text:
        logger.fatal("Error: Cannot provide both --user-prompt-file and --user-prompt-text. Choose one.")
        sys.exit(1)
    if not args.user_prompt_file and not args.user_prompt_text and not args.demo:
        logger.info("No user prompt provided. Using default built-in prompt.")

    # Profile Source
    if args.profile and args.profile_file:
        logger.fatal("Error: Cannot provide both --profile and --profile-file. Choose one.")
        sys.exit(1)
    if not args.profile and not args.profile_file and not args.demo:
        logger.info("No profile specified. Using default built-in profile.")

    # Ollama URL
    if args.ollama_url:
        try:
            _normalize_ollama_url(args.ollama_url) # Just validate, actual assignment happens later
        except ValueError as e:
            logger.fatal(f"Error: {e}")
            sys.exit(1)

    # Numeric Ranges
    if args.max_iterations is not None and args.max_iterations < 1:
        logger.fatal(f"Error: --max-iterations must be a positive integer (>= 1). Received: {args.max_iterations}")
        sys.exit(1)
    if args.quality_threshold is not None and not (0.0 <= args.quality_threshold <= 1.0):
        logger.fatal(f"Error: --quality-threshold must be between 0.0 and 1.0. Received: {args.quality_threshold}")
        sys.exit(1)
    if args.change_threshold is not None and not (0.0 <= args.change_threshold <= 1.0):
        logger.fatal(f"Error: --change-threshold must be between 0.0 and 1.0. Received: {args.change_threshold}")
        sys.exit(1)
    # --- End Validation ---

    # Handle --demo flag
    if args.demo:
        logger.info("Running in demo mode. Overriding some settings.")
        user_input = DEFAULT_USER_PROMPT # Use default prompt for demo
        llm_configs = AVAILABLE_LLMS_BY_PROFILE["Fast_Lightweight"] # Use a lightweight profile for demo
        system_config = SystemConfig(
            ollama_host=DEFAULT_CONFIG.ollama_host,
            max_iterations=3, # Shorter iterations for demo
            quality_threshold=0.7, # Lower quality for faster demo
            change_threshold=0.2, # Higher change tolerance for demo
            log_level="INFO",
            enable_sandbox=False, # No sandbox for quick demo
            enable_human_approval=False, # No human approval for quick demo
        )
    else:
        # Determine user input
        user_input = DEFAULT_USER_PROMPT
        if args.user_prompt_file:
            try:
                user_input = _read_prompt_from_file(Path(args.user_prompt_file))
                logger.debug(f"Prompt read from '{args.user_prompt_file}'. Length = {len(user_input)}")
            except (FileNotFoundError, RuntimeError) as e:
                logger.fatal(f"Error reading user prompt file: {e}")
                sys.exit(1)
        elif args.user_prompt_text:
            user_input = args.user_prompt_text
            logger.debug(f"User prompt provided as text. Length = {len(user_input)}")

        # Determine LLM configurations
        llm_configs: Dict[str, LLMConfig] = {}
        if args.profile_file:
            try:
                llm_configs = _load_profile_from_file(Path(args.profile_file))
                logger.info(f"Successfully loaded custom profile from '{args.profile_file}'.")
            except (FileNotFoundError, RuntimeError, TypeError, ValueError) as e:
                logger.fatal(f"Error loading profile from file '{args.profile_file}': {e}")
                sys.exit(1)
        elif args.profile:
            if args.profile not in AVAILABLE_LLMS_BY_PROFILE:
                logger.fatal(f"Error: Unknown profile '{args.profile}'. Available profiles: {', '.join(AVAILABLE_LLMS_BY_PROFILE.keys())}")
                sys.exit(1)
            llm_configs = AVAILABLE_LLMS_BY_PROFILE[args.profile]
            logger.info(f"Using built-in profile: {args.profile}")
        else:
            # Default to a sensible profile if none specified
            default_profile_name = "High_Reasoning" # Or another suitable default
            llm_configs = AVAILABLE_LLMS_BY_PROFILE[default_profile_name]
            logger.info(f"No profile specified, using default: {default_profile_name}")

        # Construct SystemConfig from arguments and defaults
        system_config = SystemConfig(
            ollama_host=_normalize_ollama_url(args.ollama_url) if args.ollama_url else DEFAULT_CONFIG.ollama_host,
            max_iterations=args.max_iterations if args.max_iterations is not None else DEFAULT_CONFIG.max_iterations,
            quality_threshold=args.quality_threshold if args.quality_threshold is not None else DEFAULT_CONFIG.quality_threshold,
            change_threshold=args.change_threshold if args.change_threshold is not None else DEFAULT_CONFIG.change_threshold,
            log_level=log_level,
            enable_sandbox=args.enable_sandbox if args.enable_sandbox is not None else DEFAULT_CONFIG.enable_sandbox,
            enable_human_approval=args.enable_human_approval if args.enable_human_approval is not None else DEFAULT_CONFIG.enable_human_approval,
            # Add other SystemConfig parameters here as they become available in args
        )

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
    # ---------------------------------------------------------------------------

    # --- Dry Run ---
    if args.dry_run:
        logger.info("Dry run enabled. Skipping actual workflow execution and deliverable saving.")
        logger.info("--- Dry Run Summary ---")
        logger.info(f"User Input (first 100 chars): {user_input[:100]}...")
        logger.info(f"System Config: {system_config.model_dump_json(indent=2)}")
        logger.info(f"LLM Configs (first role): {list(llm_configs.keys())[0] if llm_configs else 'N/A'}")
        if llm_configs:
            for role, cfg in llm_configs.items():
                logger.info(f"  Role '{role}': model={cfg.model_id}  temp={cfg.temperature}")
        logger.info("-----------------------")
        return # Exit here for dry run

    try:
        # Initialise and run workflow
        workflow = GraphWorkflow(system_config, llm_configs)
        logger.info(f"Starting workflow with input: {user_input[:100]}...")
        final_state_dict = await workflow.run(user_input)

        class TempState:
            def __init__(self, **entries):
                self.__dict__.update(entries)

        final_state = TempState(**final_state_dict)

        output_dir = Path("deliverables")
        saved_dir, timestamp = await save_deliverables(final_state, output_dir)
        
        logger.info("=== WORKFLOW SUMMARY ===")
        logger.info(f"Iterations completed: {final_state.iteration_count}")
        logger.info(f"Quality evaluations: {len(final_state.quality_evaluations)}")
        logger.info(f"Deliverables saved to: {saved_dir}")
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
        sys.exit(1)


# -------------------------------------------------------------------------------- #


# ---------- Profile Command Functions ------------------------------------------- #
USER_PROFILES_DIR = Path.home() / ".coopllm" / "profiles"
USER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

def get_user_profiles_dir() -> Path:
    # This function is now redundant but kept for potential external use or clarity
    return USER_PROFILES_DIR

# -------------------------------------------------------------------------------- #


# ---------- Config Command Functions -------------------------------------------- #
def get_user_config_file() -> Path:
    path = Path.home() / ".coopllm" / "config.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def _get_all_profiles() -> Dict[str, Dict[str, LLMConfig]]:
    """Returns a dictionary of all available profiles (built-in and user-defined)."""
    all_profiles = AVAILABLE_LLMS_BY_PROFILE.copy()
    for profile_file in USER_PROFILES_DIR.glob("*.yaml"):
        try:
            profile_name = profile_file.stem
            # Use _load_profile_from_file to validate structure
            all_profiles[profile_name] = _load_profile_from_file(profile_file)
        except Exception as e:
            # Log a warning but don't exit, as other profiles might be valid
            print(f"Warning: Could not load user profile '{profile_file.name}': {e}", file=sys.stderr)
    return all_profiles

def _save_user_profile(profile_name: str, file_path: Path):
    """Saves a profile from a given file path to the user profiles directory."""
    target_path = USER_PROFILES_DIR / f"{profile_name}.yaml"
    try:
        # Validate the content before saving
        _load_profile_from_file(file_path) 
        target_path.write_bytes(file_path.read_bytes())
        print(f"Profile '{profile_name}' added successfully from '{file_path}'.")
    except Exception as e:
        print(f"Error adding profile '{profile_name}': {e}", file=sys.stderr)
        sys.exit(1)

def _delete_user_profile(profile_name: str):
    """Deletes a user-defined profile."""
    profile_file = USER_PROFILES_DIR / f"{profile_name}.yaml"
    if profile_file.is_file():
        try:
            profile_file.unlink()
            print(f"Profile '{profile_name}' deleted successfully.")
        except Exception as e:
            print(f"Error deleting profile '{profile_name}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: User-defined profile '{profile_name}' not found.", file=sys.stderr)
        sys.exit(1)


async def profile_command(args: argparse.Namespace):
    """Handles profile management commands."""
    logger = setup_logging(DEFAULT_CONFIG.log_level) # Setup basic logging for profile commands

    if args.profile_subcommand == "list":
        all_profiles = _get_all_profiles()
        print("\nAvailable LLM Profiles:")
        print("-----------------------")
        for name, profile_configs in all_profiles.items():
            source = "(Built-in)" if name in AVAILABLE_LLMS_BY_PROFILE else "(User-defined)"
            print(f"- {name} {source}")
            for role, config in profile_configs.items():
                print(f"    {role.replace('_', ' ').title()}: {config.model_id} (temp={config.temperature})")
        print("-----------------------")
    elif args.profile_subcommand == "show":
        profile_name = args.name
        all_profiles = _get_all_profiles()
        if profile_name in all_profiles:
            print(f"\nDetails for Profile '{profile_name}':")
            print("---------------------------")
            for role, config in all_profiles[profile_name].items():
                print(f"  {role.replace('_', ' ').title()}:")
                print(f"    Model ID: {config.model_id}")
                print(f"    Temperature: {config.temperature}")
                print(f"    Max Tokens: {config.max_tokens}")
            print("---------------------------")
        else:
            logger.fatal(f"Error: Profile '{profile_name}' not found.")
            sys.exit(1)
    elif args.profile_subcommand == "add":
        profile_name = args.name
        file_path = Path(args.file)
        _save_user_profile(profile_name, file_path)
    elif args.profile_subcommand == "delete":
        profile_name = args.name
        _delete_user_profile(profile_name)


# -------------------------------------------------------------------------------- #


# ---------- Config Command Functions -------------------------------------------- #
USER_CONFIG_FILE = Path.home() / ".coopllm" / "config.yaml"
USER_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

def _load_user_config() -> SystemConfig:
    """
    Loads user-defined SystemConfig from ~/.coopllm/config.yaml, merging with DEFAULT_CONFIG.
    """
    user_config_data = {}
    if USER_CONFIG_FILE.is_file():
        try:
            with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_config_data = yaml.safe_load(f)
            if not isinstance(user_config_data, dict):
                print(f"Warning: User config file '{USER_CONFIG_FILE}' is not a valid YAML dictionary. Using default config.", file=sys.stderr)
                user_config_data = {}
        except yaml.YAMLError as exc:
            print(f"Warning: Invalid YAML format in user config file '{USER_CONFIG_FILE}': {exc}. Using default config.", file=sys.stderr)
            user_config_data = {}
        except Exception as exc:
            print(f"Warning: Failed to read user config file '{USER_CONFIG_FILE}': {exc}. Using default config.", file=sys.stderr)
            user_config_data = {}
    
    # Merge user config with default config
    # Pydantic's parse_obj_as or direct instantiation handles defaults well
    return SystemConfig(**{**DEFAULT_CONFIG.model_dump(), **user_config_data})

def _save_user_config(config: SystemConfig):
    """
    Saves the current SystemConfig to ~/.coopllm/config.yaml.
    """
    try:
        with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config.model_dump(), f, indent=2)
        print(f"Configuration saved to '{USER_CONFIG_FILE}'.")
    except Exception as e:
        print(f"Error saving configuration to '{USER_CONFIG_FILE}': {e}", file=sys.stderr)
        sys.exit(1)

async def config_command(args: argparse.Namespace):
    """
    Handles system configuration commands.
    """
    logger = setup_logging(DEFAULT_CONFIG.log_level) # Setup basic logging for config commands

    if args.config_subcommand == "show":
        current_config = _load_user_config()
        print("\nCurrent System Configuration:")
        print("-----------------------------")
        for key, value in current_config.model_dump().items():
            print(f"  {key}: {value}")
        print("-----------------------------")
    elif args.config_subcommand == "set":
        key = args.key
        value = args.value
        current_config = _load_user_config()
        if hasattr(current_config, key):
            try:
                # Attempt to cast value to the correct type based on SystemConfig model
                field_type = SystemConfig.model_fields[key].annotation
                if field_type == bool:
                    if value.lower() == 'true':
                        setattr(current_config, key, True)
                    elif value.lower() == 'false':
                        setattr(current_config, key, False)
                    else:
                        raise ValueError(f"Invalid boolean value for {key}: {value}")
                elif field_type == int:
                    setattr(current_config, key, int(value))
                elif field_type == float:
                    setattr(current_config, key, float(value))
                elif field_type == Path:
                    setattr(current_config, key, Path(value))
                else:
                    setattr(current_config, key, value)
                
                _save_user_config(current_config)
                print(f"Configuration updated: {key} = {value}")
            except ValueError as e:
                logger.fatal(f"Error: Invalid value for config key '{key}': {e}")
                sys.exit(1)
            except Exception as e:
                logger.fatal(f"Error setting config key '{key}': {e}")
                sys.exit(1)
        else:
            logger.fatal(f"Error: Unknown configuration key: '{key}'.")
            sys.exit(1)
    elif args.config_subcommand == "edit":
        editor = os.environ.get('EDITOR', 'notepad' if sys.platform == 'win32' else 'vim')
        try:
            print(f"Opening '{USER_CONFIG_FILE}' in {editor}...")
            os.system(f'{editor} {USER_CONFIG_FILE}')
        except Exception as e:
            logger.fatal(f"Error opening editor: {e}")
            sys.exit(1)
    elif args.config_subcommand == "reset":
        if USER_CONFIG_FILE.is_file():
            try:
                USER_CONFIG_FILE.unlink()
                print(f"User configuration file '{USER_CONFIG_FILE}' deleted. Using default settings.")
            except Exception as e:
                logger.fatal(f"Error deleting user config file: {e}")
                sys.exit(1)
        else:
            print("No user configuration file found. Already using default settings.")


# -------------------------------------------------------------------------------- #


# ---------- Custom Help Formatter ----------------------------------------------- #
class CustomHelpFormatter(argparse.HelpFormatter):
    def _format_action(self, action):
        # Customize how arguments are displayed
        if action.option_strings:
            return '  %s %s\n' % (', '.join(action.option_strings), self._format_action_dest(action))
        return super()._format_action(action)

    def _format_action_dest(self, action):
        # Don't display the default metavar for positional arguments
        return ''

    def _get_help_string(self, action):
        help_string = action.help
        if '%(default)s' not in action.help and action.default is not argparse.SUPPRESS:
            if action.default is None and action.type is not bool: # Don't show None for bool flags
                help_string += ' (default: None)'
            elif action.default is not None:
                help_string += ' (default: %s)' % action.default
        return help_string

    def _format_usage(self, usage, actions, groups, prefix):
        if usage is argparse.SUPPRESS:
            return ''
        usage = super()._format_usage(usage, actions, groups, prefix)
        return usage.replace('usage: ', 'Usage: ')


# -------------------------------------------------------------------------------- #


# ---------- Debug Command Functions --------------------------------------------- #
async def debug_command(args: argparse.Namespace):
    """Handles debug commands."""
    logger = setup_logging(DEFAULT_CONFIG.log_level)

    if args.debug_subcommand == "log":
        log_file = Path("debug.log") # Assuming debug.log is in the current directory
        if log_file.is_file():
            try:
                print(f"\n--- Content of {log_file} ---")
                with open(log_file, 'r', encoding='utf-8') as f:
                    print(f.read())
                print(f"--- End of {log_file} ---")
            except Exception as e:
                logger.fatal(f"Error reading log file {log_file}: {e}")
                sys.exit(1)
        else:
            print(f"No debug log file found at {log_file}.")


# -------------------------------------------------------------------------------- #


# ---------- Info Command Functions ---------------------------------------------- #
async def info_command(args: argparse.Namespace):
    """Handles info commands."""
    if args.info_subcommand == "version":
        print("Cooperative LLM CLI Version: 0.1.0")
    elif args.info_subcommand == "system":
        print("\n--- System Information ---")
        print(f"Operating System: {platform.system()} {platform.release()} ({platform.version()})")
        print(f"Python Version: {sys.version}")
        print(f"Current Working Directory: {os.getcwd()}")
        print(f"User home: {Path.home()}")
        print("-------------------------")


# -------------------------------------------------------------------------------- #


# ---------- Main CLI Entry Point ------------------------------------------------ #
async def cli_main():
    parser = argparse.ArgumentParser(
        description="Cooperative LLM System CLI",
        formatter_class=CustomHelpFormatter # Use custom formatter
    )

    # Global options (e.g., --version, --help)
    parser.add_argument(
        "--version", action="version", version="%(prog)s 0.1.0" # Placeholder version
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Run Command ---
    run_parser = subparsers.add_parser(
        "run", help="Execute the cooperative LLM workflow",
        formatter_class=CustomHelpFormatter,
        epilog="""
Examples:
  # 1. Run with default settings (uses built-in prompt and High_Reasoning profile)
  python cli.py run

  # 2. Run with a custom prompt file and a specific built-in profile
  python cli.py run -U prompts/my_feature.txt -P Fast_Lightweight

  # 3. Run with a custom profile file and increased iterations
  python cli.py run -F my_custom_profile.yaml -M 5

  # 4. Run in demo mode (quick, lightweight settings)
  python cli.py run --demo

  # 5. Run with debug logging enabled
  python cli.py run --debug -U prompts/my_feature.txt
"""
    )

    # Argument Groups for 'run' command
    input_options = run_parser.add_argument_group('Input Options')
    input_options.add_argument(
        "-U", "--user-prompt-file", type=str,
        help="Path to a file containing the user prompt."
    )
    input_options.add_argument(
        "--user-prompt-text", type=str,
        help="Directly provide the user prompt as a string. Overrides --user-prompt-file if both are given."
    )

    profile_options = run_parser.add_argument_group('Profile Options')
    profile_options.add_argument(
        "-P", "--profile", type=str,
        help=f"Name of a built-in LLM profile. Available: {', '.join(AVAILABLE_LLMS_BY_PROFILE.keys())}"
    )
    profile_options.add_argument(
        "-F", "--profile-file", type=str,
        help="Path to a custom YAML file defining LLM configurations for roles."
    )

    workflow_control = run_parser.add_argument_group('Workflow Control')
    workflow_control.add_argument(
        "-M", "--max-iterations", type=int,
        help=f"Maximum number of workflow iterations."
    )
    workflow_control.add_argument(
        "-Q", "--quality-threshold", type=float,
        help=f"Minimum quality score required to halt the workflow."
    )
    workflow_control.add_argument(
        "-C", "--change-threshold", type=float,
        help=f"Minimum change magnitude to detect stagnation."
    )
    workflow_control.add_argument(
        "-S", "--enable-sandbox", action=argparse.BooleanOptionalAction,
        help=f"Enable or disable the sandboxed development environment."
    )
    workflow_control.add_argument(
        "-A", "--enable-human-approval", action=argparse.BooleanOptionalAction,
        help=f"Enable or disable human approval step."
    )
    workflow_control.add_argument(
        "--demo", action="store_true",
        help="Run in demo mode with quick, lightweight settings. Overrides other run options."
    )
    workflow_control.add_argument(
        "--dry-run", action="store_true",
        help="Simulate the workflow without executing LLM calls or saving deliverables."
    )

    ollama_options = run_parser.add_argument_group('Ollama Settings')
    ollama_options.add_argument(
        "-O", "--ollama-url", type=str,
        help=f"URL of the Ollama host."
    )

    logging_options = run_parser.add_argument_group('Logging Options')
    logging_options.add_argument(
        "--log-level", type=str, choices=["debug", "info", "warning", "error", "critical"],
        help=f"Set the logging verbosity level."
    )
    logging_options.add_argument(
        "--debug", action="store_true",
        help="Enable verbose debug logging. Equivalent to --log-level debug."
    )

    run_parser.set_defaults(func=run_command)

    # --- Profile Command ---
    profile_parser = subparsers.add_parser(
        "profile", help="Manage LLM profiles",
        formatter_class=CustomHelpFormatter
    )
    profile_subparsers = profile_parser.add_subparsers(
        dest="profile_subcommand", required=True, help="Profile commands"
    )

    # Profile list
    profile_list_parser = profile_subparsers.add_parser(
        "list", help="List all available LLM profiles (built-in and user-defined)",
        formatter_class=CustomHelpFormatter
    )
    profile_list_parser.set_defaults(func=profile_command)

    # Profile show
    profile_show_parser = profile_subparsers.add_parser(
        "show", help="Display details of a specific LLM profile",
        formatter_class=CustomHelpFormatter
    )
    profile_show_parser.add_argument(
        "name", type=str, help="Name of the profile to show"
    )
    profile_show_parser.set_defaults(func=profile_command)

    # Profile add
    profile_add_parser = profile_subparsers.add_parser(
        "add", help="Add a custom LLM profile from a YAML file",
        formatter_class=CustomHelpFormatter
    )
    profile_add_parser.add_argument(
        "name", type=str, help="Name to assign to the new profile"
    )
    profile_add_parser.add_argument(
        "file", type=str, help="Path to the YAML file defining the profile"
    )
    profile_add_parser.set_defaults(func=profile_command)

    # Profile delete
    profile_delete_parser = profile_subparsers.add_parser(
        "delete", help="Delete a user-defined LLM profile",
        formatter_class=CustomHelpFormatter
    )
    profile_delete_parser.add_argument(
        "name", type=str, help="Name of the profile to delete"
    )
    profile_delete_parser.set_defaults(func=profile_command)

    # --- Config Command ---
    config_parser = subparsers.add_parser(
        "config", help="Manage system configurations",
        formatter_class=CustomHelpFormatter
    )
    config_subparsers = config_parser.add_subparsers(
        dest="config_subcommand", required=True, help="Configuration commands"
    )

    # Config show
    config_show_parser = config_subparsers.add_parser(
        "show", help="Display the current effective system configuration",
        formatter_class=CustomHelpFormatter
    )
    config_show_parser.set_defaults(func=config_command)

    # Config set
    config_set_parser = config_subparsers.add_parser(
        "set", help="Set a specific configuration key-value pair",
        formatter_class=CustomHelpFormatter
    )
    config_set_parser.add_argument(
        "key", type=str, help="Configuration key to set (e.g., ollama_host)"
    )
    config_set_parser.add_argument(
        "value", type=str, help="Value to set for the configuration key"
    )
    config_set_parser.set_defaults(func=config_command)

    # Config edit
    config_edit_parser = config_subparsers.add_parser(
        "edit", help="Open the user configuration file in a text editor",
        formatter_class=CustomHelpFormatter
    )
    config_edit_parser.set_defaults(func=config_command)

    # Config reset
    config_reset_parser = config_subparsers.add_parser(
        "reset", help="Reset user configuration to default settings",
        formatter_class=CustomHelpFormatter
    )
    config_reset_parser.set_defaults(func=config_command)

    # --- Debug Command ---
    debug_parser = subparsers.add_parser(
        "debug", help="Diagnostic and debugging utilities",
        formatter_class=CustomHelpFormatter
    )
    debug_subparsers = debug_parser.add_subparsers(
        dest="debug_subcommand", required=True, help="Debug commands"
    )

    # Debug log sub-command
    debug_log_parser = debug_subparsers.add_parser(
        "log", help="Display a summary of recent log entries or the entire log file",
        formatter_class=CustomHelpFormatter
    )
    debug_log_parser.set_defaults(func=debug_command)

    # --- Info Command ---
    info_parser = subparsers.add_parser(
        "info", help="Display system information",
        formatter_class=CustomHelpFormatter
    )
    info_subparsers = info_parser.add_subparsers(
        dest="info_subcommand", required=True, help="Information commands"
    )

    # Info version sub-command
    info_version_parser = info_subparsers.add_parser(
        "version", help="Display CLI version",
        formatter_class=CustomHelpFormatter
    )
    info_version_parser.set_defaults(func=info_command)

    # Info system sub-command
    info_system_parser = info_subparsers.add_parser(
        "system", help="Display system and environment details",
        formatter_class=CustomHelpFormatter
    )
    info_system_parser.set_defaults(func=info_command)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Ensure log level is correctly set before passing to functions
    if hasattr(args, 'log_level') and args.debug:
        args.log_level = "debug"
    elif not hasattr(args, 'log_level'):
        args.log_level = DEFAULT_CONFIG.log_level # Fallback for commands without explicit --log-level

    await args.func(args)


if __name__ == "__main__":
    asyncio.run(cli_main())