"""
LangGraph node implementations for the cooperative LLM workflow.
This module wires together the different LLM roles (PM, architect, programmer, tester, reviewer) into a
re‑entrant workflow that keeps iterating until a quality gate signals that the solution is ready.
"""

# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #
import time
import logging
from typing import Dict, Any, TypedDict

# LangGraph provides the `StateGraph` helper that lets us define nodes, edges and conditional logic.
from langgraph.graph import StateGraph, END

# Application specific imports – replace with your own if needed.
from models.llm_manager import LLMManager
from workflow.quality_gate import QualityGate
from config.settings import AVAILABLE_LLMS, DEFAULT_CONFIG
from utils.prompts import get_prompt
from utils.logging_config import log_node_execution

# --------------------------------------------------------------------------- #
# TypedDict that defines the shape of the state that flows through the graph.
# Every node receives the current state, mutates it and returns the updated state.
# --------------------------------------------------------------------------- #
class WorkflowState(TypedDict):
    """State management for the workflow."""
    user_input: str               # Original user prompt
    requirements: str            # Product‑manager output
    design: str                  # Architect design
    code: str                    # Programmer source code
    test_results: str            # Tester results
    review_feedback: str         # Reviewer comments
    deliverables: Dict[str, str] # Mapping of deliverable name → text
    iteration_count: int         # How many iterations have been run
    quality_evaluations: list    # List of dicts with each quality‑gate evaluation
    should_halt: bool            # Flag set by the quality gate

# --------------------------------------------------------------------------- #
# Main graph class – instantiates sub‑components, builds the graph and provides
# a public `run()` helper that kicks off the whole workflow.
# --------------------------------------------------------------------------- #
class CooperativeLLMGraph:
    """LangGraph implementation for cooperative LLM workflow."""

    def __init__(self, config=DEFAULT_CONFIG):
        """Initialize the workflow graph."""
        self.config = config

        # Manager that knows how to call the underlying LLMs (OpenAI, Gemini, etc.)
        self.llm_manager = LLMManager(config)

        # Quality gate uses two thresholds: a minimum score and a change‑threshold
        self.quality_gate = QualityGate(
            self.llm_manager,
            config.quality_threshold,
            config.change_threshold
        )

        self.logger = logging.getLogger("coop_llm.graph")

        # Build and compile the StateGraph – this creates the runtime graph
        self.graph = self._build_graph()

    # ----------------------------------------------------------------------- #
    # Graph construction
    # ----------------------------------------------------------------------- #
    def _build_graph(self):
        """Build the LangGraph workflow."""
        # Create a StateGraph that will use our `WorkflowState` dict as the state type.
        workflow = StateGraph(WorkflowState)

        # ------------------------------------------------------------------- #
        # Register each node – each is an async function that mutates the state.
        # ------------------------------------------------------------------- #
        workflow.add_node("requirements_analysis", self.requirements_analysis_node)
        workflow.add_node("system_design", self.system_design_node)
        workflow.add_node("code_implementation", self.code_implementation_node)
        workflow.add_node("testing_debugging", self.testing_debugging_node)
        workflow.add_node("review_refinement", self.review_refinement_node)
        workflow.add_node("quality_gate", self.quality_gate_node)
        workflow.add_node("output_generation", self.output_generation_node)

        # ------------------------------------------------------------------- #
        # Define deterministic edges – the workflow proceeds linearly.
        # ------------------------------------------------------------------- #
        workflow.add_edge("requirements_analysis", "system_design")
        workflow.add_edge("system_design"  + "review_refinement", "code_implementation", )
        workflow.add_edge("code_implementation", "testing_debugging")
        workflow.add_edge("testing_debugging", "review_refinement")
        workflow.add_edge("review_refinement", "quality_gate")

        # ------------------------------------------------------------------- #
        # Conditional edges from the quality gate – depending on the evaluation
        # we either continue looping or exit to output generation.
        # ------------------------------------------------------------------- #
        workflow.add_conditional_edges(
            "quality_gate",
            self._should_continue,
            {
                # "continue": "requirements_analysis",
                "continue": "system_design",
                "halt": "output_generation"
            }
        )

        # ------------------------------------------------------------------- #
        # Entry point of the graph and final exit
        # ------------------------------------------------------------------- #
        workflow.set_entry_point("requirements_analysis")
        # workflow.set_entry_point("system_design")
        workflow.add_edge("output_generation", END)

        # Compile to produce a runnable graph object.
        return workflow.compile()

    # ----------------------------------------------------------------------- #
    # Node implementations – each node receives the current state and returns the updated state.
    # The implementation pattern is the same for all nodes:
    #   * record start time
    #   * build the LLM prompt
    #   * call the LLM
    #   * compress if configured
    #   * update state and deliverables
    #   * log execution metrics
    #   * handle errors
    # ----------------------------------------------------------------------- #

    # ------------------------------------------------------------------- #
    # 1. Product Manager – produces the high‑level requirements
    # ------------------------------------------------------------------- #
    async def requirements_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Product Manager analyzes requirements."""
        start_time = time.time()

        llm_config = AVAILABLE_LLMS["product_manager"]
        prompt = get_prompt(
            "product_manager",
            user_input=state["user_input"],
            context=f"Iteration: {state['iteration_count']}"
        )

        try:
            response = await self.llm_manager.generate_response(llm_config, prompt)

            # Optional compression – useful when the LLM output is huge.
            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response)

            # Persist the results in the state and in the deliverables map
            state["requirements"] = response
            state["deliverables"]["requirements"] = response

            execution_time = time.time() - start_time
            log_node_execution(
                self.logger,
                "Requirements Analysis",
                {"user_input": state["user_input"]},
                {"requirements": response},
                execution_time
            )
        except Exception as e:
            self.logger.error(f"Error in requirements analysis: {e}")
            state["requirements"] = f"Error in requirements analysis: {e}"

        return state

    # ------------------------------------------------------------------- #
    # 2. Architect – designs the system architecture
    # ------------------------------------------------------------------- #
    async def system_design_node(self, state: WorkflowState) -> WorkflowState:
        """Architect designs the system."""
        start_time = time.time()

        llm_config = AVAILABLE_LLMS["architect"]
        prompt = get_prompt(
            "architect",
            requirements=state.requirements,
            context=f"Iteration: {state.iteration_count}"
        )

        try:
            response = await self.llm_manager.generate_response(llm_config, prompt)

            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response)

            state["design"] = response
            state["deliverables"]["design"] = response

            execution_time = time.time() - start_time
            log_node_execution(
                self.logger,
                "System Design",
                {"requirements": state.requirements},
                {"design": response},
                execution_time
            )
        except Exception as e:
            self.logger.error(f"Error in system design: {e}")
            state["design"] = f"Error in system design: {e}"

        return state

    # ------------------------------------------------------------------- #
    # 3. Programmer – writes the source code
    # ------------------------------------------------------------------- #
    async def code_implementation_node(self, state: WorkflowState) -> WorkflowState:
        """Programmer implements the code."""
        start_time = time.time()

        llm_config = AVAILABLE_LLMS["programmer"]
        prompt = get_prompt(
            "programmer",
            design=state.design,
            context=f"Iteration: {state.iteration_count}"
        )

        try:
            response = await self.llm_manager.generate_response(llm_config, prompt)

            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response)

            state["code"] = response
            state["deliverables"]["code"] = response

            execution_time = time.time() - start_time
            log_node_execution(
                self.logger,
                "Code Implementation",
                {"design": state.design},
                {"code": response},
                execution_time
            )
        except Exception as e:
            self.logger.error(f"Error in code implementation: {e}")
            state["code"] = f"Error in code implementation: {e}"

        return state

    # ------------------------------------------------------------------- #
    # 4. Tester – validates the implementation
    # ------------------------------------------------------------------- #
    async def testing_debugging_node(self, state: WorkflowState) -> WorkflowState:
        """Tester validates the implementation."""
        start_time = time.time()

        llm_config = AVAILABLE_LLMS["tester"]
        prompt = get_prompt(
            "tester",
            code=state.code,
            requirements=state.requirements,
            context=f"Iteration: {state.iteration_count}"
        )

        try:
            response = await self.llm_manager.generate_response(llm_config, prompt)

            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response)

            state["test_results"] = response
            state["deliverables"]["test_results"] = response

            execution_time = time.time() - start_time
            log_node_execution(
                self.logger,
                "Testing & Debugging",
                {"code": state.code, "requirements": state.requirements},
                {"test_results": response},
                execution_time
            )
        except Exception as e:
            self.logger.error(f"Error in testing: {e}")
            state["test_results"] = f"Error in testing: {e}"

        return state

    # ------------------------------------------------------------------- #
    # 5. Reviewer – gives feedback & proposes refinements
    # ------------------------------------------------------------------- #
    async def review_refinement_node(self, state: WorkflowState) -> WorkflowState:
        """Reviewer provides feedback and refinement."""
        start_time = time.time()

        llm_config = AVAILABLE_LLMS["reviewer"]
        # Turn the deliverables dict into a plain string to feed into the prompt
        deliverables_text = "\n\n".join([f"{k}: {v}" for k, v in state.deliverables.items()])

        prompt = get_prompt(
            "reviewer",
            deliverables=deliverables_text,
            context=f"Iteration: {state.iteration_count}"
        )

        try:
            response = await self.llm_manager.generate_response(llm_config, prompt)

            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response)

            state["review_feedback"] = response
            state["deliverables"]["review_feedback"] = response

            execution_time = time.time() - start_time
            log_node_execution(
                self.logger,
                "Review & Refinement",
                {"deliverables": deliverables_text},
                {"review_feedback": response},
                execution_time
            )
        except Exception as e:
            self.logger.error(f"Error in review: {e}")
            state["review_feedback"] = f"Error in review: {e}"

        return state

    # ------------------------------------------------------------------- #
    # 6. Quality Gate – decides whether the iteration should continue
    # ------------------------------------------------------------------- #
    async def quality_gate_node(self, state: WorkflowState) -> WorkflowState:
        """Quality gate evaluation."""
        start_time = time.time()

        # Previous evaluation snapshot – None if this is the first pass
        previous_state = None
        if state.quality_evaluations:
            previous_state = state.quality_evaluations[-1].get("state_snapshot")

        # Current snapshot that will be evaluated
        current_state_snapshot = {
            "requirements": state.requirements,
            "design": state.design,
            "code": state.code,
            "test_results": state.test_results,
            "review_feedback": state.review_feedback,
        }

        try:
            # `evaluate_state` returns (should_halt, evaluation_dict)
            should_halt, evaluation = await self.quality_gate.evaluate_state(
                current_state_snapshot, previous_state
            )

            state["should_halt"] = should_halt
            state["iteration_count"] += 1

            # Store the evaluation together with the snapshot and iteration number
            evaluation["state_snapshot"] = current_state_snapshot
            evaluation["iteration"] = state.iteration_count
            state["quality_evaluations"].append(evaluation)

            execution_time = time.time() - start_time
            log_node_execution(
                self.logger,
                "Quality Gate",
                {"current_state": current_state_snapshot},
                {"evaluation": evaluation},
                execution_time
            )
        except Exception as e:
            self.logger.error(f"Error in quality gate: {e}")
            # If we cannot evaluate, stop after the configured maximum iterations.
            state["should_halt"] = state.iteration_count >= self.config.max_iterations

        return state

    # ------------------------------------------------------------------- #
    # 7. Output Generation – collates everything into the final deliverable set
    # ------------------------------------------------------------------- #
    async def output_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Generate final outputs and deliverables."""
        start_time = time.time()

        final_deliverables = {
            "requirements_specification": state.requirements,
            "system_design": state.design,
            "source_code": state.code,
            "test_results": state.test_results,
            "review_feedback": state.review_feedback,
            "quality_evaluations": state.quality_evaluations,
            "iteration_count": state.iteration_count,
        }

        # Merge with any existing deliverables (e.g. partial ones from earlier passes)
        state["deliverables"].update(final_deliverables)

        execution_time = time.time() - start_time
        log_node_execution(
            self.logger,
            "Output Generation",
            {"iteration_count": state.iteration_count},
            {"final_deliverables": list(final_deliverables.keys())},
            execution_time
        )

        self.logger.info("🎉 WORKFLOW COMPLETED SUCCESSFULLY")
        return state

    # ------------------------------------------------------------------- #
    # Helper that the graph uses to decide the next edge after the quality gate.
    # ------------------------------------------------------------------- #
    def _should_continue(self, state: WorkflowState) -> str:
        """Return the name of the edge to follow from the quality gate."""
        if state.should_halt or state.iteration_count >= self.config.max_iterations:
            return "halt"
        return "continue"

    # ------------------------------------------------------------------- #
    # Public entry point – users call this to run a full workflow.
    # ------------------------------------------------------------------- #
    async def run(self, user_input: str) -> WorkflowState:
        """Execute the complete workflow."""
        self.logger.info("🚀 STARTING COOPERATIVE LLM WORKFLOW")

        # Initialise the state dictionary – TypedDict members that are not set default to None
        initial_state: WorkflowState = {
            "user_input": user_input,
            "requirements": "",
            "design": "",
            "code": "",
            "test_results": "",
            "review_feedback": "",
            "deliverables": {},
            "iteration_count": 0,
            "quality_evaluations": [],
            "should_halt": False,
        }

        try:
            final_state = await self.graph.ainvoke(initial_state)
            return final_state
        except Exception as e:
            self.logger.error(f"Error in workflow execution: {e}")
            raise