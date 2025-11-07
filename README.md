# MyChatDev - Cooperative LLM System with Ollama

A Python program that enables cooperative interaction between multiple locally hosted LLMs using Ollama, orchestrated through LangGraph workflows.

## Author

- **Author:** Jones Chung
- **Email:** jones.developer.chung@gmail.com

## 🏗️ Architecture

The system implements a **Multi-Layered Validation Workflow** where different LLMs take on specialized roles, orchestrated through a **graph-based state machine using LangGraph**. The key to this architecture is a series of fast, iterative loops that validate the work at each stage, including a sandboxed environment for code development and a reflective mechanism for overcoming stagnation.

### Agent Roles
- **Product Manager**: Analyzes initial requirements (derived from the user's prompt) and consults the system's **Experience/Memory**.
- **System Architect**: Creates the high-level technical design based on the Product Manager's requirements.
- **Tester**: Generates unit tests and **executes them within a sandboxed environment** to validate the code, using the Programmer's code and the Product Manager's requirements as input.
- **Programmer**: A **tool-using agent** that works within a sandboxed environment to write, compile, and test code until it passes the required checks, incorporating feedback from the Tester and Reviewer, and guided by the System Architect's design.
- **Code Reviewer**: Performs a holistic review of the validated code for logic, style, and maintainability, providing actionable feedback based on all previous deliverables.
- **Quality Gate**: A system agent that performs a rubric-based quality assessment and **adaptively decides whether to halt, continue, or trigger reflection** based on the current state of all deliverables.
- **Reflector**: A system agent that performs root-cause analysis when the workflow stagnates and proposes **strategic guidance** based on quality evaluations.
- **Distiller**: A system agent that intelligently compresses content to preserve context.

## 📁 Project Structure

```
MyChatDev/
├── src/
│   ├── cli.py                     # Main CLI entry point and orchestration
│   ├── main.py                    # Main application entry point
│   ├── example_usage.py           # Example usage script
│   ├── config/                  # Configuration files
│   ├── workflow/                # Workflow logic
│   ├── utils/                   # Utility functions
│   ├── models/                  # LLM models
│   └── prompts/                 # Prompt templates
├── tests/
│   └── ...                      # Test files
├── docs/
│   └── ...                      # Documentation files
├── logs/
│   └── ...                      # Log files
├── .gitignore                 # Git ignore file
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Ollama is running:**
   ```bash
   ollama serve
   ```

3. **Verify required models are available:**
   ```bash
   ollama list
   ```

## 🎯 Usage

## 🚀 Usage

The Cooperative LLM CLI now features a structured command-line interface with sub-commands for different functionalities.

### Global Options

*   `--version`: Display the CLI version.
*   `--help`: Show general help message.

### `run` command: Execute the cooperative LLM workflow

This is the primary command for executing the multi-agent LLM workflow.

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

### `profile` command: Manage LLM profiles

This command allows you to list, show details, add, or delete LLM profiles.

**Examples:**

*   **1. List all available LLM profiles (built-in and user-defined):**
    ```bash
    python src/cli.py profile list
    ```

*   **2. Display details of a specific LLM profile:**
    ```bash
    python src/cli.py profile show High_Reasoning
    ```

*   **3. Add a custom LLM profile from a YAML file:**
    ```bash
    python src/cli.py profile add my_new_profile /path/to/my_profile.yaml
    ```
    Custom profiles are stored in `~/.coopllm/profiles/`.

*   **4. Delete a user-defined LLM profile:**
    ```bash
    python src/cli.py profile delete my_old_profile
    ```

### `config` command: Manage system configurations

This command allows you to view, set, edit, or reset system-wide configurations.

**Examples:**

*   **1. Display the current effective system configuration:**
    ```bash
    python src/cli.py config show
    ```

*   **2. Set a specific configuration key-value pair:**
    ```bash
    python src/cli.py config set ollama_host http://192.168.1.100:11434
    ```

*   **3. Open the user configuration file in a text editor:**
    ```bash
    python src/cli.py config edit
    ```
    This opens `~/.coopllm/config.yaml`.

*   **4. Reset user configuration to default settings:**
    ```bash
    python src/cli.py config reset
    ```

### `debug` command: Diagnostic and debugging utilities

This command provides tools for debugging the CLI.

**Examples:**

*   **1. Display the content of the debug log file:**
    ```bash
    python src/cli.py debug log
    ```

### `info` command: Display system information

This command provides information about the CLI and the system environment.

**Examples:**

*   **1. Display CLI version:**
    ```bash
    python src/cli.py info version
    ```

*   **2. Display system and environment details:**
    ```bash
    python src/cli.py info system
    ```

## 🔧 Configuration

The Cooperative LLM CLI provides dedicated sub-commands to manage LLM profiles and system-wide configurations.

### LLM Profiles

LLM profiles define the specific LLM models and parameters assigned to each agent role (e.g., Product Manager, Programmer, Tester). You can manage these profiles using the `profile` sub-command.

*   **Listing Profiles:** To see all available built-in and user-defined profiles:
    ```bash
    python src/cli.py profile list
    ```

*   **Showing Profile Details:** To inspect the configuration of a specific profile:
    ```bash
    python src/cli.py profile show High_Reasoning
    ```

*   **Adding Custom Profiles:** You can define your own profiles in YAML files and add them to the CLI:
    ```bash
    python src/cli.py profile add MyCustomProfile /path/to/my_profile.yaml
    ```
    Custom profiles are stored in `~/.coopllm/profiles/`.

*   **Deleting Custom Profiles:** To remove a user-defined profile:
    ```bash
    python src/cli.py profile delete MyCustomProfile
    ```

### System Parameters

System-wide parameters (e.g., Ollama host, iteration limits, sandbox settings) are managed via the `config` sub-command. These settings are stored in `~/.coopllm/config.yaml`.

*   **Showing Current Configuration:** To view the active system configuration:
    ```bash
    python src/cli.py config show
    ```

*   **Setting Parameters:** To change a specific parameter:
    ```bash
    python src/cli.py config set ollama_host http://192.168.1.100:11434
    ```

*   **Editing Configuration File:** To open the configuration file in your default editor for advanced changes:
    ```bash
    python src/cli.py config edit
    ```

*   **Resetting Configuration:** To revert all user-defined settings to system defaults:
    ```bash
    python src/cli.py config reset
    ```


## 🎛️ Quality Gate System

The system includes an intelligent quality gate that uses a rubric-based assessment to evaluate the deliverables. Instead of a single score, it rates the output on multiple criteria (e.g., `correctness`, `completeness`, `readability`).

- **Rubric-Based Scoring**: Provides detailed, actionable feedback to the agents.
- **Overall Quality Score**: A weighted average of the rubric scores, used to determine if the quality threshold is met.
- **Change Magnitude**: Amount of change between iterations (0-1).
- **Automatic Halting**: Stops when the quality threshold is met or changes are minimal.

### Quality Gate Behavior

- **HALT** when `overall_quality_score` ≥ 0.8 OR `change_magnitude` ≤ 0.1
- **TRIGGER SELF-CORRECTION** if `overall_quality_score` stagnates for multiple iterations.
- **CONTINUE** otherwise (up to `max_iterations`).

## 📊 Logging and Debugging

### Comprehensive Logging

-   **Refined Levels**: Logging messages are categorized into FATAL, ERROR, WARNING, INFO, and DEBUG levels for precise monitoring.
-   **Node Execution**: Detailed logs for each workflow step
-   **Timestamps**: All operations timestamped
-   **Input/Output Tracking**: Size and content logging
-   **Error Handling**: Detailed error reporting

### Log Files

Logs are saved to `logs/coop_llm_YYYYMMDD_HHMMSS.log` (or `debug.log` for the `debug log` command).

### Debugging with the CLI

*   **Enable Debug Logging for `run` command:** Use the `--debug` flag with the `run` command to enable verbose debug logging. This is equivalent to `--log-level debug`.
    ```bash
    python src/cli.py run --debug -U prompts/my_feature.txt
    ```

*   **View Debug Log File:** Use the `debug log` command to display the content of the `debug.log` file (if it exists in the current working directory).
    ```bash
    python src/cli.py debug log
    ```

## 📦 Deliverables

The system generates:

- **requirements_specification.md** - Analyzed requirements
- **system_design.md** - Architectural design
- **source_code.py** - Implementation code
- **test_results.md** - Testing and validation results
- **review_feedback.md** - Code review feedback
- **strategic_guidance.md** - Strategic guidance from the Reflector (if triggered)
- **complete_state.json** - Full workflow state

## 🧪 Testing

Run unit tests:

```bash
pytest tests/
```

Run specific test:

```bash
pytest tests/test_llm_manager.py::TestLLMManager::test_generate_response_success
```

## 📈 Evaluation Metrics

To systematically evaluate the system's performance and identify areas for improvement, we will track the following key metrics:

- **Success Rate**: The percentage of user prompts that result in a "HALT" decision from the Quality Gate with an `overall_quality_score` above the `quality_threshold`.
- **Iteration Count**: The number of iterations required to reach a successful "HALT" state. Lower iteration counts indicate higher efficiency.
- **Code Quality**: Assessed by the `overall_quality_score` from the Quality Gate, which is a weighted average of rubric scores (e.g., correctness, completeness, readability).
- **Time to Completion**: The total elapsed time from the initial user prompt to the final "HALT" decision.
- **Stagnation Rate**: The frequency with which the Reflector agent is triggered, indicating how often the system encounters and attempts to overcome stagnation.

## 🔄 Workflow Process: The Multi-Layered Validation Workflow

The system avoids the "all or nothing" approach of a single, long iteration. Instead, it uses a series of nested feedback loops to ensure quality and correctness at each step.

### Phase 1: Strategic Planning

1.  **Requirements Analysis**: The **Product Manager** analyzes the user's prompt, pulling relevant information from the **Experience/Memory** knowledge base. If `strategic_guidance` is available from a previous reflection, it is incorporated here.
2.  **System Design**: The **System Architect** creates the technical blueprint for the project. If `strategic_guidance` is available, it is incorporated here.
3.  **Human Approval (Optional)**: If `enable_human_approval` is set to `True`, the high-level plan and design can be presented to a human operator for approval before entering the development phase. The workflow pauses until approval or rejection.

### Phase 2: Sandboxed Development

This phase replaces a simple code generation step with a powerful, self-contained development environment.

1.  **Sandbox Invocation**: A temporary, isolated directory is created and populated with the design documents and unit tests.
2.  **Iterative Development**: The **Programmer** agent is activated within the sandbox. Its goal is to make the tests pass. It works in a self-correcting loop, incorporating `review_feedback` and `strategic_guidance` if available:
    *   **Code**: Writes source code (e.g., `main.c`, `main.py`) and build files (e.g., a `Makefile`) using a `write_file` tool.
    *   **Compile/Execute**: Executes a compiler (e.g., `make` or `gcc`) or interpreter (e.g., `python`) using a `run_shell_command` tool. If it fails, it reads the error, debugs its code, and retries.
    *   **Test**: Once the code compiles/executes, it runs the unit tests (e.g., `pytest`). If they fail, it reads the failure logs, debugs its code, and retries the compile-and-test cycle.
3.  **Submission**: Once all tests pass, the agent calls a special `submit_deliverable` tool, and the validated code is passed to the next phase.

### Phase 3: Holistic Review and Refinement

Once the Sandboxed Development phase produces code that is syntactically valid and passes all unit tests, it moves to the outer loop for a holistic review.

1.  **Test Generation & Execution**: The **Tester** agent generates a suite of unit tests based on the system design and code, and then **executes these tests within the sandbox**. The results are used to validate the implementation.
2.  **Code Review**: The **Code Reviewer** assesses the code for broader qualities like logic, efficiency, and maintainability, providing `review_feedback`.
3.  **Adaptive Quality Gate**: The **Quality Gate** agent evaluates the entire project against a detailed rubric.
    *   **If Quality is Met**: The workflow is complete. The final deliverables are generated, and the **Experience/Memory** is updated with the learnings from the project.
    *   **If Quality Stagnates**: The **Reflector** agent is triggered to perform root-cause analysis and propose `strategic_guidance`, which is then fed into the next iteration (starting back at Phase 1). Stagnation is detected if the `overall_quality_score` does not significantly improve over `stagnation_iterations`.
    *   **If Quality Improves but not Met**: The detailed feedback is passed to the agents for the next full iteration, starting back at Phase 1.
## 🎨 Design Principles

- **Multi-Layered Validation**: Catch errors early and often with nested feedback loops (immediate sanity checks, static analysis, unit tests, and a final quality gate).
- **Ground-Truth Validation**: Ground LLMs in reality by integrating external, non-AI tools like compilers, linters, and test runners.
- **Fail Fast, Retry Fast**: Use small, rapid inner loops (e.g., the Development Sub-Loop) to fix technical errors, reserving expensive, full-iteration loops for strategic changes.
- **Actionable, Rubric-Based Feedback**: Provide specific, structured feedback to agents rather than a single, generic score.
- **Right Tool for the Job**: Use a heterogeneous mix of models—large models for complex reasoning and smaller, faster models for analytical and constrained tasks.
- **Configurability**: Avoid hardcoded values; all agent models and key parameters should be user-configurable.
- **Observability**: Maintain detailed logging for debugging and performance analysis.

## 🔧 Extending the System

### Extensibility via Plugin System (Future Development)

The CLI is being designed with an extensibility via plugin system in mind. This will allow users to:

*   Implement and register custom workflow nodes.
*   Integrate alternative LLM providers or models.
*   Add new sub-commands to the CLI.

For detailed design concepts and future plans regarding the plugin system, please refer to the `DEVELOPMENT_LOG.md`.


## 🚨 Troubleshooting

### Common Issues

1.  **Model Not Available**
    *   If you encounter errors like `ERROR: LLM Model '<model_name>' required for <role> is not available...`, it means the required LLM is not available on your Ollama instance.
    *   For the `--demo` mode, the `Fast_Lightweight` profile is used, which typically requires `gemma3:4b`, `deepseek-coder:6.7b`, and `neural-chat:latest`.
    *   To make a model available, pull it using the Ollama CLI:
        ```bash
        ollama pull <model_name:tag>
        # Example for demo models:
        # ollama pull gemma3:4b
        # ollama pull deepseek-coder:6.7b
        # ollama pull neural-chat:latest
        ```
    *   You can list available models with `ollama list`.

2.  **Connection Error**
    *   Ensure Ollama is running: `ollama serve`
    *   Check your Ollama host configuration using `python src/cli.py config show` or specify it with `python src/cli.py run -O <ollama_host_url>`.

3.  **Memory Issues / Ollama Runner Crashes**
    *   This can manifest as `llama runner process has terminated` errors.
    *   Ensure your system has sufficient RAM for the models you are running.
    *   Try using smaller models (e.g., with the `Low_Reasoning` profile: `python src/cli.py run -P Low_Reasoning ...`).
    *   Restart your Ollama server.
    *   Enable compression (if available in `SystemConfig`): `python src/cli.py config set enable_compression true`.

4.  **Graph Recursion Limit Managed Dynamically**
    *   This used to manifest as `GraphRecursionError: Recursion limit of X reached`.
    *   **Solution:** The `recursion_limit` is now dynamically managed by the system based on the `--max-iterations` CLI argument. This ensures that the internal graph recursion limit is automatically adjusted to accommodate longer workflows, reducing the likelihood of this error for typical use cases. If this error still occurs, consider if your workflow logic has unintended infinite loops or if `max_iterations` is set to an extremely high value. Analyze logs and deliverables to understand workflow progression.

5.  **Quality Gate LLM Not Returning Valid JSON**
    *   This can manifest as `LLM assessment is not valid JSON` warnings and the workflow getting stuck in a loop.
    *   **Cause:** The LLM assigned to the Quality Gate role is not consistently adhering to the strict JSON output format specified in its prompts.
    *   **Solution:**
        *   **Model Selection:** Ensure you are using a sufficiently capable LLM for the Quality Gate role (e.g., `gemma3:4b` or larger models are generally better at strict instruction following than `tinyllama`).
        *   **Prompt Review:** Carefully review `config/system_quality_gate_prompt.txt` and `config/quality_gate_prompt.txt` to ensure the instructions for JSON output are clear, unambiguous, and strongly emphasized.
        *   **Parsing Robustness:** The system includes robust parsing logic, with enhancements to sanitize JSON (e.g., replacing single quotes with double quotes, removing trailing commas) and a more flexible regex for extracting JSON from markdown blocks. However, consistent JSON output from the LLM is paramount for accurate assessment.

### Enhanced CLI Messages

*   **Startup Information**: The CLI now provides more detailed startup messages, including the selected LLM profile, its source (named, file, or default), the configured Ollama host, and the source of the user prompt.
*   **Actionable Error Messages**: Error messages, especially for missing LLM models, are now more specific and include actionable advice on how to resolve the issue (e.g., `ollama pull <model_name>`).

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the logs in `logs/` directory
- Review configuration in `src/config/settings.py`
- Run tests to verify functionality
- Enable debug logging for detailed troubleshooting
