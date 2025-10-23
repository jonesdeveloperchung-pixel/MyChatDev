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

1.  **`config/settings.py`:** This file defines the default system-wide parameters (`SystemConfig`) and the structure for LLM configurations (`LLMConfig`).
2.  **`config/llm_profiles.py`:** This file defines different LLM profiles, each mapping agent roles to specific LLM models, temperatures, and other parameters.

### LLM Model Assignment

You can customize which LLM models are used for each agent role by editing `config/llm_profiles.py`. Different profiles (e.g., `high_reasoning`, `low_reasoning`) are provided to suit various needs for speed and reasoning capability.

### System Parameters

System-wide parameters like `max_iterations`, `quality_threshold`, `enable_sandbox`, etc., are defined in `config/settings.py`.

## 🎯 Running the System

The primary way to interact with the system is through the `cli.py` script.

### Basic Execution

To run the system with default settings and a predefined prompt:

```bash
python cli.py
```

### Running via CLI with Custom Parameters

The `cli.py` script provides extensive command-line arguments to customize the workflow.

```bash
python cli.py -P <profile_name> -U <prompt_file_path> --debug --url <ollama_host_url> --max_iterations <num> --enable_sandbox <true/false> ...
```

**Key CLI Arguments:**

*   `-P, --profile <profile_name>`: Selects an LLM profile (e.g., `high_reasoning`, `medium_reasoning`, `low_reasoning`). Default is `high_reasoning`.
*   `-U, --user_prompt <prompt_file_path>`: Path to a file containing the user prompt. If omitted, a built-in default prompt is used.
*   `-D, --debug`: Enables debug-level logging for more detailed output.
*   `-O, --ollama_url <ollama_host_url>`: Specifies the URL of the Ollama host (e.g., `http://localhost:11434`). Overrides the `ollama_host` in `config/settings.py`.
*   `--max_iterations <num>`: Maximum number of iterations the workflow will run.
*   `--enable_sandbox <true/false>`: Master switch to enable or disable the sandboxed development environment.
*   `--quality_threshold <float>`: Sets the quality score threshold for the Quality Gate.
*   `--change_threshold <float>`: Sets the change magnitude threshold for the Quality Gate (stagnation).
*   `-T, --stagnation_iterations <num>`: Number of iterations to check for stagnation before triggering the Reflector agent.
*   `--enable_human_approval <true/false>`: Enables or disables the optional human approval step after system design.

**Example:**

To run with the `low_reasoning` profile, a specific prompt, debug logging, a custom Ollama URL, 3 max iterations, and sandbox enabled:

```bash
python cli.py -P low_reasoning -U prompts/python_factorial.txt -D -O http://localhost:11434 --max_iterations 3 --enable_sandbox true -T 3
```

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

The `main.py` script includes a framework for running multiple test cases and collecting performance data. After running `main.py`, a `performance_summary_YYYYMMDD_HHMMSS.json` file will be generated in the `deliverables/` folder, summarizing key metrics for each test case.

Key metrics to analyze include:
*   **Success Rate**: Percentage of prompts leading to a successful halt.
*   **Iteration Count**: Efficiency of the workflow.
*   **Code Quality**: Final `overall_quality_score` from the Quality Gate.
*   **Time to Completion**: Total execution time.
*   **Stagnation Rate**: How often the Reflector is triggered.

## 🚨 Troubleshooting

Refer to the "Troubleshooting" section in `README.md` for common issues and solutions.

---