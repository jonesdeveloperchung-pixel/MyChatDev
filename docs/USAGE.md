# USAGE Guide for Cooperative LLM System

This guide provides detailed instructions on how to set up, configure, run, and interpret the outputs of the Cooperative LLM System.

## 🚀 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/MyChatDev.git
    cd MyChatDev
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ensure Ollama is running:**
    The system relies on Ollama for local LLM inference. Make sure your Ollama server is running.
    ```bash
    ollama serve
    ```

4.  **Verify required models are available:**
    Check if the models specified in your chosen LLM profile (e.g., `high_reasoning`, `low_reasoning`) are downloaded and available in Ollama.
    ```bash
    ollama list
    ```
    If a model is missing, download it:
    ```bash
    ollama pull model-name:tag
    ```

## 🔧 Configuration

The system's behavior can be configured in two primary ways:

1.  **`src/config/settings.py`:** This file defines the default system-wide parameters (`SystemConfig`) and the structure for LLM configurations (`LLMConfig`).
2.  **`src/config/llm_profiles.py`:** This file defines different LLM profiles, each mapping agent roles to specific LLM models, temperatures, and other parameters.

### LLM Model Assignment

You can customize which LLM models are used for each agent role by editing `src/config/llm_profiles.py`. Different profiles (e.g., `high_reasoning`, `low_reasoning`) are provided to suit various needs for speed and reasoning capability.

### System Parameters

System-wide parameters like `max_iterations`, `quality_threshold`, `enable_sandbox`, etc., are defined in `src/config/settings.py`.

## 🧪 Testing

A comprehensive test plan is available in `docs/TEST_PLAN.md`. This document outlines test cases for all CLI commands and options, ensuring the quality and reliability of the application.

To execute the tests, please refer to the instructions in `docs/TEST_PLAN.md`.

## 🎯 Running the System

The primary way to interact with the system is through the `src/cli.py` script.

### `run` Command

The `run` command is the primary entry point for executing the cooperative LLM workflow.

**Examples:**

*   **1. Run with default settings (uses built-in prompt and High_Reasoning profile):**
    ```bash
    python src/cli.py run
    ```

*   **2. Run with a custom prompt file and a specific built-in profile:**
    ```bash
    python src/cli.py run -U prompts/my_feature.txt -P Fast_Lightweight
    ```

*   **3. Run with a custom profile file and increased iterations:**
    ```bash
    python src/cli.py run -F my_custom_profile.yaml -M 5
    ```

*   **4. Run in demo mode (quick, lightweight settings):**
    ```bash
    python src/cli.py run --demo
    ```
    This uses a default prompt and the `Fast_Lightweight` profile, with shorter iterations and disabled sandboxing/human approval for a quick demonstration.

*   **5. Run with debug logging enabled:**
    ```bash
    python src/cli.py run --debug -U prompts/my_feature.txt
    ```

*   **6. Simulate a run without execution or saving deliverables (Dry Run):**
    ```bash
    python src/cli.py run --dry-run -U prompts/my_feature.txt
    ```

*   **7. Specify a custom output directory for deliverables:**
    ```bash
    python src/cli.py run -U prompts/my_feature.txt --output-dir my_custom_deliverables
    ```

**Key `run` Command Arguments:**

*   `-U, --user-prompt-file <file_path>`: Path to a file containing the user prompt.
*   `--user-prompt-text <string>`: Directly provide the user prompt as a string.
*   `-P, --profile <profile_name>`: Selects an LLM profile (e.g., `High_Reasoning`, `Low_Reasoning`).
*   `-F, --profile-file <file_path>`: Path to a custom YAML file defining LLM configurations for roles.
*   `-M, --max-iterations <num>`: Maximum number of workflow iterations.
*   `-Q, --quality-threshold <float>`: Minimum quality score required to halt the workflow.
*   `-C, --change-threshold <float>`: Minimum change magnitude to detect stagnation.
*   `-S, --enable-sandbox <true/false>`: Enable or disable the sandboxed development environment.
*   `-A, --enable-human-approval <true/false>`: Enable or disable human approval step.
*   `--demo`: Run in demo mode with quick, lightweight settings.
*   `--dry-run`: Simulate the workflow without executing LLM calls or saving deliverables.
*   `-O, --ollama-url <ollama_host_url>`: URL of the Ollama host.
*   `--log-level <level>`: Set the logging verbosity level (debug, info, warning, error, critical).
e*   `--debug`: Enable verbose debug logging. Equivalent to `--log-level debug`.

It's important to understand how prompts are utilized across different LLM roles within the system:

*   **Initial User Prompt (`-U` parameter):** The content provided via the `-U` parameter (or the built-in default prompt) serves as the primary input for the **Product Manager** role. This role is responsible for analyzing and refining these initial requirements.
*   **Subsequent Role Inputs:** For all other LLM roles (e.g., Architect, Programmer, Tester, Reviewer, Reflector), their main input is typically the *deliverables* or outputs generated by preceding roles in the workflow. They do not directly receive the original user prompt. This iterative process ensures that each role builds upon the work of the previous one, refining the solution progressively.

## ✨ User Experience Enhancements

To improve usability and provide clearer feedback, the CLI has been enhanced with:

-   **Detailed Startup Information**: When you run `src/cli.py`, it now provides comprehensive startup messages, including the selected LLM profile (name or file path), its source (named, file, or default), the configured Ollama host, and the source of the user prompt.
-   **Actionable Error Messages**: Error messages, particularly for missing LLM models, are now more specific and include actionable advice on how to resolve the issue (e.g., suggesting `ollama pull <model_name>`). This helps users quickly diagnose and fix configuration problems.

## 📦 Interpreting Deliverables

Upon completion, the system generates a timestamped folder in the `deliverables/` directory (e.g., `deliverables/20251021-144343`). This folder contains:

*   **`requirements_specification.md`**: The detailed requirements analyzed by the Product Manager.
*   **`system_design.md`**: The architectural design created by the System Architect.
*   **`source_code.py`**: The implemented code from the Programmer agent.
*   **`test_results.md`**: The results of test generation and execution by the Tester agent.
*   **`review_feedback.md`**: Feedback from the Code Reviewer.
*   **`strategic_guidance.md`**: Guidance from the Reflector agent (if triggered).
*   **`complete_state.json`**: A JSON file containing the full workflow state, including iteration counts, quality evaluations, and final decisions.

## 📈 Performance Analysis

The `src/main.py` includes a framework for running multiple test cases and collecting performance data. After running `src/main.py`, a `performance_summary_YYYYMMDD_HHMMSS.json` file will be generated in the `deliverables/` folder, summarizing key metrics for each test case.

Key metrics to analyze include:
*   **Success Rate**: Percentage of prompts leading to a successful halt.
*   **Iteration Count**: Efficiency of the workflow.
*   **Code Quality**: Final `overall_quality_score` from the Quality Gate.
*   **Time to Completion**: Total execution time.
*   **Stagnation Rate**: How often the Reflector is triggered.

## 🚨 Troubleshooting

Refer to the "Troubleshooting" section in `README.md` for common issues and solutions.

### Common Issues (Specific to Quality Gate LLM)

1. **Quality Gate LLM Not Returning Valid JSON**
   - This can manifest as `LLM assessment is not valid JSON` warnings and the workflow getting stuck in a loop.
   - **Cause:** The LLM assigned to the Quality Gate role is not consistently adhering to the strict JSON output format specified in its prompts.
   - **Solution:**
     - **Model Selection:** Ensure you are using a sufficiently capable LLM for the Quality Gate role (e.g., `gemma3:4b` or larger models are generally better at strict instruction following than `tinyllama`).
     - **Prompt Review:** Carefully review `src/config/system_quality_gate_prompt.txt` and `src/config/quality_gate_prompt.txt` to ensure the instructions for JSON output are clear, unambiguous, and strongly emphasized.
     - **Parsing Robustness:** The system includes robust parsing logic, but consistent JSON output from the LLM is paramount.

---