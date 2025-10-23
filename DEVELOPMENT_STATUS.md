# Development Status

This document tracks the step-by-step implementation of the new 'Multi-Layered Validation Workflow' design.

**Phase 0: Design and Planning (Complete)**

- [X] Reviewed user logs and identified critical failure modes (agent refusal, language drift, quality stagnation).
- [X] Consolidated all proposed improvements into a unified architecture.
- [X] Updated `README.md` and `Graph.mmd` to reflect the new target design.
- [X] Established this development status log.

**Phase 1: Foundational Refactoring (Complete)**

- **Status:** The core workflow has been successfully refactored from a hardcoded `while` loop to a modular, graph-based state machine using `langgraph`.
- **Tasks:**
    - [X] Add `langgraph` to `requirements.txt`.
    - [X] Create a new `workflow/graph_workflow.py` to house the new implementation.
    - [X] Define a new graph state object.
    - [X] Convert the existing agent functions into `langgraph` nodes.
    - [X] Build the initial graph with a linear flow to match the old functionality.
    - [X] Update `main.py` and `cli.py` to use the new `graph_workflow` (Note: This was done in a previous turn, but the checkmark was missing).

**Phase 2: Configuration and Quality Gate Refactor (Complete)**

- **Status:** The core components have been refactored to be fully configurable, removing hardcoded values.
- **Tasks:**
    - [X] Refactor `quality_gate.py` to remove the hardcoded model and accept a configurable `LLMConfig`.
    - [X] Refactor `llm_manager.py` to make the compression model configurable.
    - [X] Refactor `quality_gate.py` to remove the 500-character state truncation.
    - [X] Add all new configuration flags (`enable_sandbox`, etc.) to `config/settings.py`.

**Phase 3: Implementing New Features (Complete)**

- **Goal:** Implement the advanced features from the new design onto the new graph-based foundation.

**Sprint 3: Implement Sandbox and TDD Workflow**
- [X] In `graph_workflow.py`, modify the graph to call the `Tester` node *before* the `Programmer` node.
- [X] Create a new `workflow/sandbox.py` file to encapsulate the sandbox logic.
- [X] Implement the `run_sandbox` method in `sandbox.py` which will manage the tool-using agent's inner loop.
- [X] Create a new `sandboxed_development_node` in `graph_workflow.py` that calls the `run_sandbox` method.
- [X] Update the graph in `_build_graph` to replace the old `code_implementation` node with the new `sandboxed_development_node`.

**Sprint 4: Integrate Tester with Sandbox for TDD**
- [X] Modify `graph_workflow.py` to ensure the `Tester` node can interact with the sandbox.
- [X] Implement the logic within the `Tester` node to generate tests, run them in the sandbox, and provide feedback to the `Programmer` node.
- [X] Ensure the `Programmer` node receives feedback from the `Tester` node and uses it to refine its code.

**Sprint 5: Enhanced Sandboxed Development Loop**
- [X] Implement `submit_deliverable` tool: Add a new tool to the `Sandbox` class that the Programmer agent can call to signal completion and submit the final code.
- [X] Improve Programmer Agent Prompt: Refine the prompt for the Programmer agent to explicitly guide it through the iterative process of writing code, creating build files (like `Makefile`), compiling, running tests, and debugging based on output.
- [X] Robust Error Handling in `run_sandbox`: Enhance the `run_sandbox` method to better parse and react to compilation and test errors, providing more structured feedback to the Programmer LLM.
- [X] Integrate `Makefile` generation: Guide the Programmer LLM to generate a `Makefile` for compilation and testing, making the sandbox more flexible for different project types.

**Sprint 6: Adaptive Review and Reflection**
- [X] Pass Review Feedback to Programmer: Modify the `GraphState` and relevant nodes to ensure `review_feedback` is accessible and actionable by the `sandboxed_development_node` in subsequent iterations. This might involve updating the prompt for the Programmer agent.
- [X] Implement Reflector Node: Create a new `reflector_node` in `graph_workflow.py` that uses the `Reflector` LLM to analyze the `quality_evaluations` and provide strategic guidance.
- [X] Conditional Edge for Reflector: Add a conditional edge after the `quality_gate_node` to invoke the `reflector_node` if quality stagnates (e.g., if `should_halt` is false but `change_magnitude` is very low for several iterations).
- [X] Integrate Reflector Output: Ensure the output of the `reflector_node` (strategic guidance) is incorporated into the `GraphState` and influences subsequent iterations.

**Sprint 7: Adaptive Quality Gate Logic**
- [X] Implement Stagnation Detection: Add logic to `decide_next_step` to detect if the `overall_quality_score` has stagnated over multiple iterations (e.g., no significant improvement or a decline).
- [X] Conditional Reflection Trigger: Based on stagnation detection, modify `decide_next_step` to return "reflect" to invoke the `reflector_node`.
- [X] Refine `decide_next_step`: Ensure the `decide_next_step` method correctly implements the "HALT", "REFLECT", and "CONTINUE" conditions as described in the `README.md`.

**Sprint 8: Refinement and Robustness**
- [X] Comprehensive Unit Testing: Develop and implement thorough unit tests for `workflow/sandbox.py`, `workflow/graph_workflow.py` (especially the new nodes and conditional logic), and `workflow/quality_gate.py` (for stagnation detection).
- [X] Prompt Optimization: Review and refine the prompts for all agents (Product Manager, Architect, Tester, Programmer, Reviewer, Reflector) to ensure they effectively utilize the new features and context (e.g., `strategic_guidance`, `review_feedback`).
- [X] Sandbox Language Support: Extend the `Sandbox` to support multiple programming languages and build systems beyond simple C/C++ (e.g., Python with `pytest`, JavaScript with `npm test`). This might involve dynamic detection of project type or user configuration.
- [X] Refine Stagnation Logic: Further refine the stagnation detection logic in `decide_next_step` to consider more complex scenarios (e.g., oscillating quality scores, long-term plateaus) and potentially introduce configurable parameters for stagnation thresholds.

**Phase 4: Evaluation and Optimization (Complete)**

**Sprint 9: Performance Evaluation and Prompt Tuning**
- [X] Define Evaluation Metrics: Establish clear metrics for evaluating the system's performance (e.g., success rate, iteration count, code quality, time to completion).
- [X] Run Test Cases: Execute a diverse set of test cases (user prompts) through the system and collect performance data.
- [X] Analyze Performance Data: Analyze the collected data to identify common failure modes, inefficiencies, and areas where agents struggle.
- [X] Prompt Tuning based on Evaluation: Based on the analysis, iteratively refine agent prompts to improve performance and address identified weaknesses.

**Sprint 10: Resource Management and External Control**
- [X] Distiller Optimization: Review and refine the `Distiller` agent's prompt and compression strategy to ensure optimal context preservation and token reduction without losing critical information. This might involve experimenting with different `compression_strategy` (e.g., `progressive_distillation` vs. `truncate`) and `max_compression_ratio` settings.
- [X] Human Approval Integration: Implement an optional "Human Approval" step in the workflow, particularly after strategic planning phases (e.g., after `system_design_node`), allowing a human operator to review and approve deliverables before proceeding. This would involve adding a new node and conditional logic.
- [ ] Dynamic Resource Allocation (Optional/Future): Explore mechanisms for dynamically adjusting LLM model sizes or configurations based on the complexity of the task or the current iteration count, to optimize for speed or accuracy. (This is a more advanced task and might be deferred).
- [ ] Cost Monitoring and Reporting (Optional/Future): Integrate tools or logging to monitor and report on LLM token usage and estimated costs, providing insights for cost optimization. (Also a more advanced task).

**Phase 5: Finalization and Documentation (Complete)**

--- 

**Project Status: COMPLETE**

--- 

**Phase 6: Workflow Persistence and Advanced State Management (Planned)**

**Goal:** Implement mechanisms to persist the workflow's state, allowing for interruption and resumption, and providing LLMs with comprehensive access to past progress and deliverables.

**Sprint 13: Workflow Checkpointing and Resumption**
- [ ] Define Persistence Strategy: Determine the best method for persisting the `GraphState` (e.g., JSON files, a simple database like SQLite, or a dedicated workflow persistence library).
- [ ] Implement Checkpointing: Modify the `GraphWorkflow` to periodically save its `GraphState` to persistent storage.
- [ ] Implement Resumption: Add functionality to `GraphWorkflow` to load a saved `GraphState` and resume execution from the last checkpoint.
- [ ] LLM Access to Historical Data: Enhance agent prompts and context management to allow LLMs to query and utilize historical `GraphState` data and deliverables from previous iterations or interrupted runs.

**Phase 7: Customization and Extensibility (Planned)**

**Goal:** Enhance the system's flexibility by allowing users to customize LLM outputs and extend its capabilities through custom templates and configurations.

**Sprint 14: Customizable Output Templates**
- [ ] Define Template Structure: Design a clear and intuitive structure for user-provided templates (e.g., using Jinja2 or a simple placeholder system).
- [ ] Implement Template Loading: Develop a mechanism to load templates from a designated `templates` folder.
- [ ] Integrate Templates into LLM Output: Modify relevant LLM agents (e.g., Product Manager for requirements, Architect for design) to use these loaded templates when generating their deliverables.
- [ ] Update Documentation: Document how users can create and use custom templates.

**Sprint 15: Enhanced Deliverable Naming and Metadata**
- [ ] Identify Key Metadata: Determine all relevant information to include in the deliverable folder name (e.g., profile, Ollama URL, prompt file name, timestamp, etc.).
- [ ] Modify Naming Convention: Update the `save_deliverables` function (in `main.py` and `cli.py`) to incorporate this metadata into the folder name.
- [ ] Update Documentation: Document the new naming convention and how to interpret the deliverable folder names.

--- 

**Phase 6: Bug Fixing and Refinement (In Progress)**

**Sprint 12: Fix `LLMManager` Integration in Sandbox**
- [X] Analyze `LLMManager` usage: Review how `LLMManager` is initialized and how `get_llm` is intended to be used.
- [X] Inspect `Sandbox` initialization: Verify that the `LLMManager` instance is correctly passed to the `Sandbox` constructor.
- [X] Correct `get_llm` call: Ensure the `get_llm` method is called correctly within the `run_sandbox` method.

**Sprint 16: Addressing Persistent LLM Output Issues**
- [X] Fixed NameError in cli.py by initializing logger earlier.
- [X] Fixed KeyError in utils/prompts.py by correctly formatting user templates.
- [X] Improved Quality Gate LLM JSON parsing robustness and model selection.
- [X] Added enable_system_prompt_files to SystemConfig and CLI.
- [ ] Enhance Test Code Generation Robustness:
    - Implement more sophisticated parsing/cleaning of generated test code in `run_tests_in_sandbox` to handle common LLM output quirks (e.g., extra conversational text, incomplete code blocks).
    - Consider adding a "code repair" step where a small LLM attempts to fix syntax errors in generated code.
    - **Long-term:** Evaluate the effectiveness of different LLM models for code generation and test generation, especially for the `tester` and `programmer` roles.
- [ ] Improve Quality Gate Reasoning Parsing:
    - Implement a more flexible parsing mechanism for the Quality Gate's reasoning, possibly using a small LLM to summarize or reformat the reasoning if direct regex parsing fails.
    - **Long-term:** Evaluate the adherence of different LLM models to strict JSON output formats.
- [ ] Address Ollama Runner Stability:
    - Investigate and document common causes for `llama runner process has terminated` errors (e.g., memory limits, model compatibility).
    - Provide clear guidance in `README.md` on how to select appropriate models and manage Ollama resources.
    - **Long-term:** Implement dynamic model switching or resource monitoring to prevent such crashes.

The Cooperative LLM System has successfully implemented the Multi-Layered Validation Workflow, including sandboxed development, adaptive quality gates, reflection, and human approval. The codebase is documented, tested, and ready for deployment or further feature expansion.

**Sprint 11: Documentation and Release Preparation**
- [X] Update `README.md`: Ensure the `README.md` is fully up-to-date with all new features, configuration options, and usage instructions. This includes the new evaluation metrics, human approval, and refined workflow.
- [X] Create `USAGE.md`: Develop a detailed `USAGE.md` guide that walks users through setting up the environment, configuring agents, running test cases, interpreting results, and leveraging advanced features like human approval and reflection.
- [X] Review and Refine Code Comments: Ensure all new code (especially in `workflow/sandbox.py`, `workflow/graph_workflow.py`, `workflow/quality_gate.py`, and `main.py`) has clear and concise comments.
- [X] Final Code Review: Conduct a final, comprehensive code review to identify any remaining bugs, inconsistencies, or areas for minor optimization.
- [X] Refined logging messages (FATAL, ERROR, WARNING, INFO, DEBUG levels).
- [X] Refined CLI arguments for user-friendliness (short and long forms).

## Phase 8: Debugging and Development Experience Improvements (Planned)

### 13. Mockup-driven Debugging for Graph Nodes

**Goal:** Significantly speed up debugging of individual graph nodes by allowing developers to isolate and test them with pre-recorded or "mocked" data.

**Suggestion:** Implement a system where each node's inputs and outputs can be stored in a dedicated "mockup folder." This allows for targeted debugging of a single node without running the entire workflow.

**Implementation Details:**

1.  **Mockup Folder Structure:**
    *   Create a configurable "mockup folder" (e.g., `mockups/`) within the project structure.
    *   Within this folder, create subdirectories for each node (e.g., `mockups/requirements_analysis/`, `mockups/system_design/`).
    *   Each node's subdirectory will contain JSON files representing the `GraphState` *before* and *after* the node's execution for specific test cases.

2.  **Mockup Generation Run:**
    *   Introduce a special "mockup generation" mode (e.g., a new CLI flag `--generate-mockups`).
    *   When enabled, the system will run a full workflow, but instead of just processing data, it will save the `GraphState` at the entry and exit of *every* node into the respective mockup folder. This creates a comprehensive dataset of node inputs and outputs.

3.  **Mockup-driven Debugging Mode:**
    *   Introduce a "mockup-driven debugging" mode (e.g., a new CLI flag `--debug-node <node_name>`).
    *   When enabled, and a specific node is targeted:
        *   **Input Mocking:** For all nodes *before* the targeted node in the workflow, the system will *load* their output `GraphState` from the mockup folder instead of actually executing them.
        *   **Targeted Execution:** The specified `<node_name>` will execute normally, taking its input from the mockup data (or the output of the preceding mocked node).
        *   **Output Mocking:** For all nodes *after* the targeted node, the system will *load* their input `GraphState` from the mockup folder and simply output their pre-recorded output, effectively skipping their execution.
        *   **Output Recording (Optional):** The output of the targeted node can optionally be saved back to its mockup file, allowing for iterative refinement of a single node's logic.

**Benefits:**
*   **Faster Iteration:** Developers can test changes to a single node in seconds or minutes, rather than waiting for a full workflow run (which can take hours).
*   **Isolated Testing:** Ensures that changes to one node don't inadvertently break others, as the inputs from other nodes are controlled.
*   **Reproducible Bugs:** Easily reproduce specific node behaviors by loading the exact input state from a mockup.
*   **Reduced LLM Costs:** Avoids unnecessary LLM calls for nodes that are not being actively debugged.
*   **Enhanced Development Experience:** Streamlines the debugging process, making it more efficient and less frustrating.

### 14. Implement Quality Gate LLM suitability testing with mockup data.

**Goal:** Systematically test all available LLMs on Ollama to determine their suitability as a Quality Gate, ensuring consistent and correctly formatted JSON output.

**Suggestion:** Develop a dedicated testing script that leverages generated mockup data to evaluate each LLM's performance against predefined criteria for Quality Gate functionality.

**Implementation Details:**

1.  **Mockup Data Generation:**
    *   Utilize the `enable_mockup_generation` flag (to be added to `SystemConfig`) to run the main workflow and capture `current_state` and `previous_state` at the entry of the `quality_gate_node`.
    *   Store these states as JSON files in a designated `mockups/quality_gate/` directory.

2.  **LLM Suitability Testing Script (`test_quality_gate_llms.py`):**
    *   **Retrieve All Ollama Models:** Use the `ollama.AsyncClient().list()` method to get a list of all models available on the configured Ollama host.
    *   **Iterate and Test:** For each available LLM model:
        *   Load a set of pre-generated mockup `current_state` and `previous_state` pairs.
        *   Instantiate `QualityGate` with the current LLM model as `gate_config`.
        *   Call `QualityGate.evaluate_state` with the mockup data.
        *   Capture the `evaluation_result` (including `quality_score`, `change_magnitude`, `decision`, `reasoning`, and `assessment_text`).
    *   **Assess Suitability:** Evaluate each LLM's output based on:
        *   **JSON Adherence:** Does the `assessment_text` consistently contain valid JSON in the expected `quality_score`, `change_magnitude`, `confidence`, `decision`, `reasoning` format?
        *   **Parsing Success:** Was `_parse_assessment` able to successfully parse the JSON without falling back to regex or returning default values?
        *   **Plausible Scores/Decisions:** Do the extracted scores and decisions seem reasonable given the input states (this might require some basic heuristics or manual review of a sample)?
    *   **Report Results:** Log detailed results for each LLM, indicating its JSON adherence, parsing success, and overall suitability for the Quality Gate role.

**Benefits:**
*   **Reliable Quality Gate:** Ensures that the Quality Gate consistently receives and correctly parses assessments, preventing workflow stagnation due to parsing errors.
*   **Informed Model Selection:** Provides data-driven insights into which LLM models are best suited for the critical Quality Gate role.
*   **Reduced Debugging Time:** Quickly identifies LLMs that struggle with strict output formats, saving development time.
*   **Improved Workflow Stability:** Contributes to a more stable and predictable workflow by using models that reliably follow instructions.

