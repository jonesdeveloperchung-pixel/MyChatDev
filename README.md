# MyChatDev - Cooperative LLM System with Ollama

A Python program that enables cooperative interaction between multiple locally hosted LLMs using Ollama, orchestrated through LangGraph workflows.

## 🏗️ Architecture

The system implements a **Multi-Layered Validation Workflow** where different LLMs take on specialized roles, orchestrated through a **graph-based state machine using LangGraph**. The key to this architecture is a series of fast, iterative loops that validate the work at each stage, including a sandboxed environment for code development and a reflective mechanism for overcoming stagnation.

### Agent Roles
- **Product Manager**: Analyzes initial requirements and consults the system's **Experience/Memory**.
- **System Architect**: Creates the high-level technical design.
- **Tester**: Generates unit tests and **executes them within a sandboxed environment** to validate the code.
- **Programmer**: A **tool-using agent** that works within a sandboxed environment to write, compile, and test code until it passes the required checks, incorporating feedback from the Tester and Reviewer.
- **Code Reviewer**: Performs a holistic review of the validated code for logic, style, and maintainability, providing actionable feedback.
- **Quality Gate**: A system agent that performs a rubric-based quality assessment and **adaptively decides whether to halt, continue, or trigger reflection**.
- **Reflector**: A system agent that performs root-cause analysis when the workflow stagnates and proposes **strategic guidance**.
- **Distiller**: A system agent that intelligently compresses content to preserve context.

## 📁 Project Structure

```
MyChatDev/
├── main.py                    # Entry point and orchestration
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── config/
│   └── settings.py           # Configuration management
├── models/
│   └── llm_manager.py        # LLM communication and management
├── workflow/
│   ├── graph_workflow.py     # LangGraph node implementations and workflow orchestration
│   ├── sandbox.py            # Sandboxed execution environment for Programmer agent
│   └── quality_gate.py       # Quality control and gatekeeper
├── utils/
│   ├── logging_config.py     # Logging configuration
│   └── prompts.py           # Centralized prompt management
└── tests/
    └── test_llm_manager.py   # Unit tests
    └── test_sandbox.py       # Unit tests for Sandbox
    └── test_graph_workflow.py # Unit tests for GraphWorkflow
    └── test_quality_gate.py  # Unit tests for QualityGate
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

### Basic Usage

```python
import asyncio
from workflow.graph_workflow import GraphWorkflow # Updated import
from config.settings import DEFAULT_CONFIG

async def main():
    # Initialize workflow
    workflow = GraphWorkflow(DEFAULT_CONFIG) # Updated class
    
    # Define your requirements
    user_input = """
    Create a Python web scraper that can:
    1. Extract product information from e-commerce websites
    2. Handle rate limiting and respect robots.txt
    3. Store data in a SQLite database
    4. Include error handling and logging
    """
    
    # Execute workflow
    final_state = await workflow.run(user_input)
    
    # Access deliverables
    print("Requirements:", final_state.deliverables['requirements'])
    print("Design:", final_state.deliverables['design'])
    print("Code:", final_state.deliverables['code'])
    print("Test Results:", final_state.deliverables['test_results'])
    print("Review Feedback:", final_state.deliverables['review_feedback'])
    print("Strategic Guidance:", final_state.deliverables['strategic_guidance'])

asyncio.run(main())
```

### Running the Complete System

```bash
python main.py
```

### Running via CLI

The `cli.py` script provides a command-line interface to run the Cooperative LLM System with various configurable parameters.

```bash
python cli.py -P <profile_name> -U <prompt_file_path> --debug --url <ollama_host_url> --max_iterations <num> --enable_sandbox <true/false> ...
```

**Key CLI Arguments:**

*   `-P, --profile <profile_name>`: Selects an LLM profile (e.g., `high_reasoning`, `medium_reasoning`, `low_reasoning`).
*   `-U, --user_prompt <prompt_file_path>`: Path to a file containing the user prompt.
*   `--debug`: Enables debug-level logging.
*   `-O, --ollama_url <ollama_host_url>`: Specifies the URL of the Ollama host (e.g., `http://localhost:11434`).
*   `--max_iterations <num>`: Maximum number of iterations for the workflow.
*   `--enable_sandbox <true/false>`: Enable or disable the sandboxed development environment.
*   `--quality_threshold <float>`: Quality score threshold for the Quality Gate.
*   `--change_threshold <float>`: Change magnitude threshold for the Quality Gate (stagnation).
*   `--stagnation_iterations <num>`: Number of iterations to check for stagnation.
*   `-Y, --enable_system_prompt_files <true/false>`: Enable or disable reading system prompts from files. If `false`, internal default system prompts are used.
*   `--enable_mockup_generation <true/false>`: Enable or disable generating mockup data for debugging graph nodes.

**Example:**

```bash
python cli.py -P low_reasoning -U prompts/python_factorial.txt -D -O http://localhost:11434 --max_iterations 3 -S true -T 3
```

## 🔧 Configuration

### LLM Model Assignment

Edit `config/llm_profiles.py` to customize model assignments. For best performance, use a mix of powerful models for complex tasks and smaller, faster models for analytical tasks.

You can select a profile using the `-P` or `--profile` command-line argument in `cli.py`. Available profiles include: `high_reasoning` (default), `medium_reasoning`, `low_reasoning`, `gemma3_phi4_gpt`, `gpt_oss`, `llama32`, `lightweight`, and `compliance`.

Example:
```bash
python cli.py -P low_reasoning -U prompts/my_prompt.txt
```

The structure of a profile in `config/llm_profiles.py` is a dictionary mapping role names to `LLMConfig` objects. Each `LLMConfig` specifies the model ID, temperature, and other parameters for a particular role.

```python
# Example of a profile (from config/llm_profiles.py)
LLM_CONFIGS_HIGH_REASONING: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(
        name="Product Manager",
        model_id="gemma3:12b",  # balance of reasoning + efficiency
        role="product_manager",
        temperature=0.4,  # slightly higher for creativity
    ),
    # ... (other roles) ...
}
```

### System Parameters

Edit `config/settings.py` to customize system-wide parameters.

Alternatively, you can override these parameters directly from the command line when running `cli.py`.

```bash
python cli.py --url http://192.168.16.120:11434 --max_iterations 10 --enable_sandbox false --quality_threshold 0.9
```

Here's an example of the `DEFAULT_CONFIG` structure, which corresponds to the configurable parameters:

```python
DEFAULT_CONFIG = SystemConfig(
    ollama_host="http://localhost:11434",  # Can be overridden by -O, --ollama_url CLI argument
    max_iterations=5,
    quality_threshold=0.8,
    change_threshold=0.1,
    log_level="INFO", # Can be overridden by -D, --debug CLI argument

    # Sandbox Settings
    enable_sandbox=True,                # Master switch for the sandboxed development environment

    # Compression Settings
    enable_compression=True,
    compression_threshold=8192,         # Content length threshold to trigger compression
    compression_strategy='progressive_distillation', # 'progressive_distillation' or 'truncate'
    max_compression_ratio=0.5,          # Prevents over-compression (e.g., 0.5 means compressed size won't be less than 50% of original)
    compression_chunk_size=8192,        # Size of chunks for progressive distillation

    # Stagnation Detection
    stagnation_iterations=3,            # Can be overridden by -T, --stagnation_iterations CLI argument

    # Human Approval
    enable_human_approval: bool = False,        # Master switch for the optional human approval step

    # System Prompt Management
    enable_system_prompt_files: bool = False,   # If True, system prompts are read from files; otherwise, internal defaults are used.

    # Mockup Generation
    enable_mockup_generation: bool = False,     # If True, generates mockup data for debugging graph nodes.
)
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

- **Refined Levels**: Logging messages are categorized into FATAL, ERROR, WARNING, INFO, and DEBUG levels for precise monitoring.
- **Node Execution**: Detailed logs for each workflow step
- **Timestamps**: All operations timestamped
- **Input/Output Tracking**: Size and content logging
- **Error Handling**: Detailed error reporting

### Log Files

Logs are saved to `logs/coop_llm_YYYYMMDD_HHMMSS.log`

### Debug Information

To enable debug-level logging, use the `-D` or `--debug` CLI flag when running `cli.py`:

```bash
python cli.py -D ...
```

Alternatively, you can set the `log_level` in `config/settings.py` to `DEBUG`.

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

### Adding New LLM Roles

1. **Define LLM Config** in `config/settings.py`:
   ```python
   "new_role": LLMConfig(
       name="New Role",
       model_id="your-model:tag",
       role="new_role"
   )
   ```

2. **Add Prompt Template** in `utils/prompts.py`:
   ```python
   NEW_ROLE = """Your role-specific prompt template..."""
   ```

3. **Create Node Function** in `workflow/graph_workflow.py`:
   ```python
   async def new_role_node(self, state: WorkflowState) -> WorkflowState:
       # Implementation
   ```

4. **Update Graph** in `_build_graph()` method

### Custom Quality Metrics

Extend `workflow/quality_gate.py` to add custom quality assessments:

```python
def custom_quality_check(self, state: WorkflowState) -> float:
    # Your custom quality logic
    return quality_score
```

## 🚨 Troubleshooting

### Common Issues

1. **Model Not Available**
   ```bash
   ollama pull model-name:tag
   ```

2. **Connection Error**
   - Ensure Ollama is running: `ollama serve`
   - Check host configuration in settings (or use `--url` CLI argument)

3. **Memory Issues / Ollama Runner Crashes**
   - This can manifest as `llama runner process has terminated` errors.
   - Ensure your system has sufficient RAM for the models you are running.
   - Try using smaller models (e.g., with the `low_reasoning` profile).
   - Restart your Ollama server.
   - Enable compression: `enable_compression=True` in `config/settings.py` (or via CLI).
   - Reduce `compression_threshold` in `config/settings.py` (or via CLI).
   - Use smaller models for non-critical roles.

4. **Graph Recursion Limit Reached**
   - This can manifest as `GraphRecursionError: Recursion limit of X reached`.
   - This indicates the workflow is iterating too many times without reaching a stop condition.
   - You can increase the limit by setting the `recursion_limit` config key (though this is not directly exposed via CLI yet).
   - More importantly, analyze the logs and deliverables to understand why the workflow is not progressing or halting. This often points to issues with agent prompts or quality gate logic.

### Performance Optimization

- Use lightweight models for summarization
- Enable message compression for long workflows
- Adjust temperature settings for consistency vs creativity
- Monitor iteration counts and quality thresholds

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
- Review configuration in `config/settings.py`
- Run tests to verify functionality
- Enable debug logging for detailed troubleshooting