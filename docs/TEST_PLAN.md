# Test Plan for MyChatDev

This document outlines the test plan for the MyChatDev CLI to ensure all commands and options work as expected.

## 1. `run` Command

The `run` command is the primary entry point for executing the cooperative LLM workflow.

| Test Case ID | Description | Command | Expected Outcome | Status |
| :--- | :--- | :--- | :--- | :--- |
| RUN-001 | Run with default settings | `python src/cli.py run` | The workflow runs with the default prompt and the "High_Reasoning" profile. Deliverables are saved to the `deliverables` directory. | **PASS** |
| RUN-002 | Run with a custom prompt file | `python src/cli.py run -U prompts/my_feature.txt` | The workflow runs with the prompt from `prompts/my_feature.txt` and the "High_Reasoning" profile. | **PASS** |
| RUN-003 | Run with a specific built-in profile | `python src/cli.py run -P Fast_Lightweight` | The workflow runs with the default prompt and the "Fast_Lightweight" profile. | **PASS** |
| RUN-004 | Run with a custom profile file | `python src/cli.py run -F my_custom_profile.yaml` | The workflow runs with the default prompt and the settings from `my_custom_profile.yaml`. | **PASS** |
| RUN-005 | Run with increased iterations | `python src/cli.py run -M 5` | The workflow runs for a maximum of 5 iterations. | **PASS** |
| RUN-006 | Run in demo mode | `python src/cli.py run --demo` | The workflow runs in demo mode with a default prompt, "Fast_Lightweight" profile, 3 iterations, and disabled sandboxing/human approval. | **PASS** |
| RUN-007 | Run with debug logging | `python src/cli.py run --debug` | The workflow runs with debug level logging. | **PASS** |
| RUN-008 | Dry run | `python src/cli.py run --dry-run` | The workflow simulates a run without executing and prints a summary. No deliverables are saved. | **PASS** |
| RUN-009 | Custom output directory | `python src/cli.py run --output-dir my_deliverables` | The deliverables are saved to the `my_deliverables` directory. | **SKIPPED** (Not Implemented) |
| RUN-010 | Invalid prompt file | `python src/cli.py run -U non_existent_file.txt` | The CLI exits with an error message that the file was not found. | **PASS** |
| RUN-011 | Invalid profile | `python src/cli.py run -P InvalidProfile` | The CLI exits with an error message that the profile is not found. | **PASS** |
| RUN-012 | Run with custom prompt text | `python src/cli.py run --user-prompt-text "Create a simple hello world program in Python."` | The workflow runs with the provided prompt text. | **PASS** |
| RUN-013 | Run with a quality threshold | `python src/cli.py run -Q 0.9` | The workflow runs and halts when the quality score is >= 0.9. | **PASS** |
| RUN-014 | Run with a change threshold | `python src/cli.py run -C 0.2` | The workflow runs and detects stagnation if the change is < 0.2. | **PASS** |
| RUN-015 | Run with sandbox enabled | `python src/cli.py run -S` | The workflow runs with the sandbox enabled. | **PASS** |
| RUN-016 | Run with human approval enabled | `python src/cli.py run -A` | The workflow pauses for human approval after the system design phase. | **PASS** |
| RUN-017 | Run with a custom Ollama URL | `python src/cli.py run -O http://custom-ollama:11434` | The workflow uses the custom Ollama URL. | **PASS** |
| RUN-018 | Run with a specific log level | `python src/cli.py run --log-level debug` | The workflow runs with debug logging. | **PASS** |
| RUN-019 | Conflict between --profile and --profile-file | `python src/cli.py run -P High_Reasoning -F my_custom_profile.yaml` | The CLI exits with an error message about the conflict. | **PASS** |
| RUN-020 | Conflict between --user-prompt-file and --user-prompt-text | `python src/cli.py run -U prompts/my_feature.txt --user-prompt-text "Hello"` | The CLI exits with an error message about the conflict. | **PASS** |

## 2. `profile` Command

The `profile` command is used to manage LLM profiles.

| Test Case ID | Description | Command | Expected Outcome | Status |
| :--- | :--- | :--- | :--- | :--- |
| PROF-001 | List all profiles | `python src/cli.py profile list` | The CLI lists all built-in and user-defined profiles. | **PASS** |
| PROF-002 | Show a specific profile | `python src/cli.py profile show High_Reasoning` | The CLI shows the details of the "High_Reasoning" profile. | **PASS** |
| PROF-003 | Add a custom profile | `python src/cli.py profile add MyProfile my_custom_profile.yaml` | The CLI adds a new profile named "MyProfile" from `my_custom_profile.yaml`. | **PASS** |
| PROF-004 | Delete a custom profile | `python src/cli.py profile delete MyProfile` | The CLI deletes the "MyProfile" profile. | **PASS** |
| PROF-005 | Show a non-existent profile | `python src/cli.py profile show NonExistentProfile` | The CLI exits with an error message that the profile was not found. | **PASS** |
| PROF-006 | Delete a non-existent profile | `python src/cli.py profile delete NonExistentProfile` | The CLI exits with an error message that the profile was not found. | **PASS** |

## 3. `config` Command

The `config` command is used to manage system configurations.

| Test Case ID | Description | Command | Expected Outcome | Status |
| :--- | :--- | :--- | :--- | :--- |
| CONF-001 | Show current configuration | `python src/cli.py config show` | The CLI shows the current system configuration, which should be the default configuration. |
| CONF-002 | Set a valid configuration value (string) | `python src/cli.py config set ollama_host http://new-host:11434` | The CLI sets the `ollama_host` to `http://new-host:11434`. The change should be reflected in `~/.coopllm/config.yaml`. |
| CONF-003 | Set a valid configuration value (integer) | `python src/cli.py config set max_iterations 10` | The CLI sets the `max_iterations` to `10`. The change should be reflected in `~/.coopllm/config.yaml`. |
| CONF-004 | Set a valid configuration value (float) | `python src/cli.py config set quality_threshold 0.9` | The CLI sets the `quality_threshold` to `0.9`. The change should be reflected in `~/.coopllm/config.yaml`. |
| CONF-005 | Set a valid configuration value (boolean) | `python src/cli.py config set enable_sandbox true` | The CLI sets the `enable_sandbox` to `True`. The change should be reflected in `~/.coopllm/config.yaml`. |
| CONF-006 | Set an invalid configuration key | `python src/cli.py config set invalid_key some_value` | The CLI exits with an error message that the key is unknown. |
| CONF-007 | Set an invalid value for a valid key (integer) | `python src/cli.py config set max_iterations not_an_integer` | The CLI exits with an error message about an invalid value. |
| CONF-008 | Set an invalid value for a valid key (float) | `python src/cli.py config set quality_threshold not_a_float` | The CLI exits with an error message about an invalid value. |
| CONF-009 | Set an invalid value for a valid key (boolean) | `python src/cli.py config set enable_sandbox not_a_boolean` | The CLI exits with an error message about an invalid value. |
| CONF-010 | Edit the configuration file | `python src/cli.py config edit` | The CLI opens the user configuration file in a text editor. |
| CONF-011 | Reset the configuration | `python src/cli.py config reset` | The CLI resets the user configuration to the default settings. `~/.coopllm/config.yaml` should be deleted. |
| CONF-012 | Show configuration after setting values | `python src/cli.py config show` | The CLI shows the updated configuration values. |
| CONF-013 | Show configuration after resetting | `python src/cli.py config show` | The CLI shows the default configuration values. |

## 4. `debug` Command

The `debug` command is used for debugging purposes.

| Test Case ID | Description | Command | Expected Outcome | Status |
| :--- | :--- | :--- | :--- | :--- |
| DEBUG-001 | Show the debug log | `python src/cli.py debug log` | The CLI shows the content of the `debug.log` file. | **PASS** |

## 5. `info` Command

The `info` command is used to display system information.

| Test Case ID | Description | Command | Expected Outcome | Status |
| :--- | :--- | :--- | :--- | :--- |
| INFO-001 | Show the version | `python src/cli.py info version` | The CLI shows the version of the application. | **PASS** |
| INFO-002 | Show system information | `python src/cli.py info system` | The CLI shows system information like OS, Python version, etc. | **PASS** |
