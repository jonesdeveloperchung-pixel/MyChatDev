"""
This module defines the new, graph-based workflow using LangGraph.
It replaces the linear, hardcoded workflow in simple_workflow.py.

Author: Jones Chung
"""

import logging
import time
from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END

from src.config.settings import SystemConfig
from src.models.llm_manager import LLMManager
from src.utils.logging_config import log_node_execution
from src.utils.prompts import get_prompt
from .quality_gate import QualityGate



# Define the state for our graph
class GraphState(TypedDict):
    """
    Represents the state of the graph workflow, holding all relevant information
    that is passed between nodes.
    """
    user_input: str
    requirements: str
    design: str
    code: str
    test_results: str
    review_feedback: str
    deliverables: Dict[str, str]
    iteration_count: int
    quality_evaluations: List[Dict[str, Any]]
    should_halt: bool
    strategic_guidance: str
    human_approval: bool # New field for human approval status
    # Potentially add fields for the new features like sandbox path, etc. later


class GraphWorkflow:
    """
    Encapsulates the logic for the LangGraph-based cooperative LLM workflow.
    """

    def __init__(self, config: SystemConfig = SystemConfig(), llm_configs: Dict[str, Any] = None):
        """
        Initializes the graph-based workflow.
        """
        self.config = config
        self.llm_manager = LLMManager(config)
        # Import here to avoid circular dependency
        from src.config.llm_profiles import AVAILABLE_LLMS_BY_PROFILE
        self.llm_configs = llm_configs or AVAILABLE_LLMS_BY_PROFILE
        self.quality_gate = QualityGate(
            self.llm_manager,
            self.llm_configs["quality_gate"],
            config.quality_threshold,
            config.change_threshold,
        )
        from .sandbox_factory import get_sandbox_implementation
        self.sandbox = get_sandbox_implementation(config, self.llm_manager, self.llm_configs)
        self.logger = logging.getLogger("coop_llm.graph_workflow")
        self.graph = self._build_graph()

    def _build_graph(self):
        """
        Builds and compiles the LangGraph state machine.
        """
        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node("requirements_analysis", self.requirements_analysis_node)
        workflow.add_node("system_design", self.system_design_node)
        workflow.add_node("sandboxed_development", self.sandboxed_development_node)
        workflow.add_node("code_generation_no_sandbox", self.code_generation_no_sandbox_node)
        workflow.add_node("testing_debugging", self.testing_debugging_node)
        workflow.add_node("review_refinement", self.review_refinement_node)
        workflow.add_node("quality_gate", self.quality_gate_node)
        workflow.add_node("human_approval", self.human_approval_node)
        workflow.add_node("reflector", self.reflector_node)
        workflow.add_node("output_generation", self.output_generation_node)

        # Define edges
        workflow.set_entry_point("requirements_analysis")
        workflow.add_edge("requirements_analysis", "system_design")
        
        # Conditional edge after system_design for human approval
        workflow.add_conditional_edges(
            "system_design",
            self.route_after_system_design, # This now directly returns the next node
            {
                "human_approval": "human_approval",
                "sandboxed_development": "sandboxed_development",
                "code_generation_no_sandbox": "code_generation_no_sandbox",
            },
        )
        # After human approval, route directly to code generation (sandboxed or not)
        workflow.add_conditional_edges(
            "human_approval",
            self.route_after_system_design, # Re-use the same routing logic
            {
                "sandboxed_development": "sandboxed_development",
                "code_generation_no_sandbox": "code_generation_no_sandbox",
            },
        )

        workflow.add_edge("sandboxed_development", "testing_debugging")
        workflow.add_edge("code_generation_no_sandbox", "testing_debugging") # Both paths lead to testing
        workflow.add_edge("testing_debugging", "review_refinement")
        workflow.add_edge("review_refinement", "quality_gate")
        
        # Conditional edge after quality gate
        workflow.add_conditional_edges(
            "quality_gate",
            self.decide_next_step,
            {
                "continue": "requirements_analysis",
                "halt": "output_generation",
                "reflect": "reflector", # New edge for reflection
            },
        )
        workflow.add_edge("reflector", "requirements_analysis") # After reflection, go back to requirements analysis
        workflow.add_edge("output_generation", END)

        # Compile the graph
        return workflow.compile()

    def decide_next_step(self, state: GraphState) -> str:
        """
        Determines the next step after the quality gate evaluation.
        """
        if state['should_halt']:
            self.logger.debug("Quality Gate decided to HALT the workflow.")
            return "halt"
        else:
            self.logger.debug("Quality Gate decided to CONTINUE or REFLECT.")
            # Check for stagnation over configurable number of iterations
            num_evaluations = len(state['quality_evaluations'])
            self.logger.debug(f"Number of quality evaluations: {num_evaluations}")
            if num_evaluations >= self.config.stagnation_iterations:
                self.logger.debug(f"Checking for stagnation over last {self.config.stagnation_iterations} iterations.")
                recent_evaluations = state['quality_evaluations'][-self.config.stagnation_iterations:]
                
                # Check if the overall_quality_score has improved significantly over these iterations
                first_score = recent_evaluations[0].get('overall_quality_score', 0)
                last_score = recent_evaluations[-1].get('overall_quality_score', 0)
                self.logger.debug(f"First score in stagnation window: {first_score:.2f}, Last score: {last_score:.2f}")

                if (last_score - first_score) < self.config.change_threshold:
                    self.logger.debug(f"Stagnation detected: change ({last_score - first_score:.2f}) below threshold ({self.config.change_threshold}). Deciding to REFLECT.")
                    return "reflect"
                else:
                    self.logger.debug(f"No stagnation detected. Deciding to CONTINUE.")
            else:
                self.logger.debug("Not enough iterations for stagnation check. Deciding to CONTINUE.")
            
            return "continue"

    def route_after_system_design(self, state: GraphState) -> str:
        """
        Determines the next step after system design, potentially routing for human approval
        or directly to code generation (sandboxed or not).
        """
        if self.config.enable_human_approval:
            return "human_approval"
        else:
            if self.config.enable_sandbox or self.config.use_mcp_sandbox:
                return "sandboxed_development"
            else:
                return "code_generation_no_sandbox"

    # --- Node Implementations ---

    async def requirements_analysis_node(self, state: GraphState) -> Dict[str, Any]:
        self.logger.info("---Executing Requirements Analysis Node---")
        start_time = time.time()
        llm_config = self.llm_configs["product_manager"]
        
        prompt_context = f"Iteration: {state['iteration_count']}"
        if state.get('strategic_guidance'):
            prompt_context += f"\nStrategic Guidance: {state['strategic_guidance']}"

        prompt_parts = get_prompt("product_manager", main_content=state['user_input'], system_config=self.config, context=prompt_context)
        self.logger.debug(f"Prompt context for Product Manager: {prompt_context}")
        messages = []
        if prompt_parts.get("system"):
            messages.append({"role": "system", "content": prompt_parts["system"]})
        messages.append({"role": "user", "content": prompt_parts["user"]})
        self.logger.debug(f"Messages sent to Product Manager: {messages}")

        try:
            response = await self.llm_manager.generate_response(llm_config, messages)
            self.logger.debug(f"Raw response from Product Manager (length {len(response)}): {response[:500]}...")
            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response, self.llm_configs["distiller"])
            
            # Update state and deliverables separately
            updated_state = {
                'requirements': response,
                'deliverables': {**state.get('deliverables', {}), 'requirements': response},
            }
            log_node_execution(self.logger, "Requirements Analysis", {"user_input": state['user_input']}, {"requirements": response}, time.time() - start_time)
        except ValueError as e:
            error_message = f"ERROR: LLM Model '{llm_config.model_id}' required for Product Manager is not available. Please pull it using 'ollama pull {llm_config.model_id}'."
            self.logger.error(error_message)
            updated_state = {'requirements': error_message}
        except Exception as e:
            self.logger.fatal(f"Error in requirements analysis: {e}")
            updated_state = {'requirements': f"Error in requirements analysis: {e}"}
        return updated_state

    async def system_design_node(self, state: GraphState) -> Dict[str, Any]:
        self.logger.info("---Executing System Design Node---")
        start_time = time.time()
        llm_config = self.llm_configs["architect"]
        
        prompt_context = f"Iteration: {state['iteration_count']}"
        if state.get('strategic_guidance'):
            prompt_context += f"\nStrategic Guidance: {state['strategic_guidance']}"

        prompt_parts = get_prompt("architect", main_content=state['requirements'], system_config=self.config, context=prompt_context)
        self.logger.debug(f"Prompt context for Architect: {prompt_context}")
        messages = []
        if prompt_parts.get("system"):
            messages.append({"role": "system", "content": prompt_parts["system"]})
        messages.append({"role": "user", "content": prompt_parts["user"]})
        self.logger.debug(f"Messages sent to Architect: {messages}")

        try:
            response = await self.llm_manager.generate_response(llm_config, messages)
            self.logger.debug(f"Raw response from Architect (length {len(response)}): {response[:500]}...")
            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response, self.llm_configs["distiller"])

            updated_state = {
                'design': response,
                'deliverables': {**state.get('deliverables', {}), 'design': response},
            }
            log_node_execution(self.logger, "System Design", {"requirements": state['requirements']}, {"design": response}, time.time() - start_time)
        except ValueError as e:
            error_message = f"ERROR: LLM Model '{llm_config.model_id}' required for System Architect is not available. Please pull it using 'ollama pull {llm_config.model_id}'."
            self.logger.error(error_message)
            updated_state = {'design': error_message}
        except Exception as e:
            self.logger.fatal(f"Error in system design: {e}")
            updated_state = {'design': f"Error in system design: {e}"}
        return updated_state



    async def sandboxed_development_node(self, state: GraphState) -> Dict[str, Any]:
        self.logger.info("---Executing Sandboxed Development Node---")
        start_time = time.time()
        try:
            sandbox_output = await self.sandbox.run_sandbox(state)
            
            if isinstance(sandbox_output, dict) and 'code_implementation' in sandbox_output:
                updated_state = {"code": sandbox_output['code_implementation'],
                                 'deliverables': {**state.get('deliverables', {}), 'code': sandbox_output['code_implementation']},
                                 **sandbox_output}
                log_node_execution(self.logger, "Sandboxed Development", {"requirements": state['requirements'], "tests": state['test_results']}, {"code": updated_state['code_implementation']}, time.time() - start_time)
                return updated_state
            else:
                # Handle cases where sandbox_output is an error string or unexpected format
                self.logger.error(f"Error in sandboxed development: Unexpected sandbox output: {sandbox_output}")
                return {"code": f"Error in sandboxed development: {sandbox_output}"}
        except Exception as e:
            self.logger.fatal(f"Error in sandboxed development: {e}")
            return {"code": f"Error in sandboxed development: {e}"}

    async def code_generation_no_sandbox_node(self, state: GraphState) -> Dict[str, Any]:
        self.logger.info("---Executing Code Generation (No Sandbox) Node---")
        start_time = time.time()
        llm_config = self.llm_configs["programmer"]

        prompt_context = f"Iteration: {state['iteration_count']}"
        if state.get('strategic_guidance'):
            prompt_context += f"\nStrategic Guidance: {state['strategic_guidance']}"
        if state.get('review_feedback'):
            prompt_context += f"\nReview Feedback: {state['review_feedback']}"

        combined_content = f"Requirements:\n{state['requirements']}\n\nSystem Design:\n{state['design']}"
        prompt_parts = get_prompt("programmer", main_content=combined_content, system_config=self.config, context=prompt_context)
        self.logger.debug(f"Prompt context for Programmer: {prompt_context}")
        messages = []
        if prompt_parts.get("system"):
            messages.append({"role": "system", "content": prompt_parts["system"]})
        messages.append({"role": "user", "content": prompt_parts["user"]})
        self.logger.debug(f"Messages sent to Programmer: {messages}")

        try:
            response = await self.llm_manager.generate_response(llm_config, messages)
            self.logger.debug(f"Raw response from Programmer (length {len(response)}): {response[:500]}...")
            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response, self.llm_configs["distiller"])

            # Write the generated code to source_code.md
            source_code_path = self.config.deliverables_path / "source_code.md"
            source_code_path.parent.mkdir(parents=True, exist_ok=True)
            with open(source_code_path, "w", encoding="utf-8") as f:
                f.write(response)
            self.logger.info(f"Generated code written to {source_code_path}")

            updated_state = {
                'code': response,
                'deliverables': {**state.get('deliverables', {}), 'code': response},
            }
            log_node_execution(self.logger, "Code Generation (No Sandbox)", {"requirements": state['requirements'], "design": state['design']}, {"code": response}, time.time() - start_time)
        except ValueError as e:
            error_message = f"ERROR: LLM Model '{llm_config.model_id}' required for Programmer is not available. Please pull it using 'ollama pull {llm_config.model_id}'."
            self.logger.error(error_message)
            updated_state = {'code': error_message}
        except Exception as e:
            self.logger.fatal(f"Error in code generation (no sandbox): {e}")
            updated_state = {'code': f"Error in code generation (no sandbox): {e}"}
        return updated_state

    async def testing_debugging_node(self, state: GraphState) -> Dict[str, Any]:
        self.logger.info("---Executing Testing & Debugging Node---")
        start_time = time.time()
        llm_config = self.llm_configs["tester"]
        
        # 1. Generate tests
        combined_content = f"Code Implementation:\n{state['code']}\n\nRequirements:\n{state['requirements']}"
        prompt_parts = get_prompt("tester", main_content=combined_content, system_config=self.config, context=f"Iteration: {state['iteration_count']}")
        self.logger.debug(f"Prompt context for Tester: Iteration: {state['iteration_count']}")
        messages = []
        if prompt_parts.get("system"):
            messages.append({"role": "system", "content": prompt_parts["system"]})
        messages.append({"role": "user", "content": prompt_parts["user"]})
        self.logger.debug(f"Messages sent to Tester: {messages}")

        try:
            generated_tests = await self.llm_manager.generate_response(llm_config, messages)
            self.logger.debug(f"Raw response from Tester (length {len(generated_tests)}): {generated_tests[:500]}...")
            if self.config.enable_compression and len(generated_tests) > self.config.compression_threshold:
                generated_tests = await self.llm_manager.compress_content(generated_tests, self.llm_configs["distiller"])

            # 2. Run tests in sandbox (conditionally)
            if self.config.enable_sandbox:
                test_execution_output = self.sandbox.run_tests_in_sandbox(state['code'], generated_tests, language="python")
                full_test_results = f"Generated Tests:\n{generated_tests}\n\nTest Execution Output:\n{test_execution_output}"
            else:
                full_test_results = f"Generated Tests:\n{generated_tests}\n\nTest execution skipped: Sandbox is disabled."
                self.logger.info("Test execution skipped because sandbox is disabled.")

            updated_state = {
                'test_results': full_test_results,
                'deliverables': {**state.get('deliverables', {}), 'test_results': full_test_results},
            }
            log_node_execution(self.logger, "Testing & Debugging", {"code": state['code'], "requirements": state['requirements']}, {"test_results": full_test_results}, time.time() - start_time)
        except ValueError as e:
            error_message = f"ERROR: LLM Model '{llm_config.model_id}' required for Tester is not available. Please pull it using 'ollama pull {llm_config.model_id}'."
            self.logger.error(error_message)
            updated_state = {'test_results': error_message}
        except Exception as e:
            self.logger.fatal(f"Error in testing: {e}")
            updated_state = {'test_results': f"Error in testing: {e}"}
        return updated_state

    async def review_refinement_node(self, state: GraphState) -> Dict[str, Any]:
        self.logger.info("---Executing Review & Refinement Node---")
        start_time = time.time()
        llm_config = self.llm_configs["reviewer"]
        deliverables_text = "\n\n".join([f"{k}: {v}" for k, v in state['deliverables'].items()])
        prompt_parts = get_prompt("reviewer", main_content=deliverables_text, system_config=self.config, context=f"Iteration: {state['iteration_count']}")
        self.logger.debug(f"Prompt context for Reviewer: Iteration: {state['iteration_count']}")
        messages = []
        if prompt_parts.get("system"):
            messages.append({"role": "system", "content": prompt_parts["system"]})
        messages.append({"role": "user", "content": prompt_parts["user"]})
        self.logger.debug(f"Messages sent to Reviewer: {messages}")

        try:
            response = await self.llm_manager.generate_response(llm_config, messages)
            self.logger.debug(f"Raw response from Reviewer (length {len(response)}): {response[:500]}...")
            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response, self.llm_configs["distiller"])

            updated_state = {
                'review_feedback': response,
                'deliverables': {**state.get('deliverables', {}), 'review_feedback': response},
            }
            log_node_execution(self.logger, "Review & Refinement", {"deliverables": deliverables_text}, {"review_feedback": response}, time.time() - start_time)
        except ValueError as e:
            error_message = f"ERROR: LLM Model '{llm_config.model_id}' required for Code Reviewer is not available. Please pull it using 'ollama pull {llm_config.model_id}'."
            self.logger.error(error_message)
            updated_state = {'review_feedback': error_message}
        except Exception as e:
            self.logger.fatal(f"Error in review: {e}")
            updated_state = {'review_feedback': f"Error in review: {e}"}
        return updated_state

    async def quality_gate_node(self, state: GraphState) -> Dict[str, Any]:
        self.logger.info("---Executing Quality Gate Node---")
        start_time = time.time()
        previous_state = state['quality_evaluations'][-1].get("state_snapshot") if state['quality_evaluations'] else None
        current_state_snapshot = {
            'requirements': state.get('requirements', ''),
            'design': state.get('design', ''),
            'code': state.get('code', ''),
            'test_results': state.get('test_results', ''),
            'review_feedback': state.get('review_feedback', ''),
        }
        
        formatted_current_state = self._format_state(current_state_snapshot)
        formatted_previous_state = self._format_state(previous_state) if previous_state else "No previous state available."
        prompt_parts = get_prompt(
            "quality_gate",
            current_state=self._format_state(current_state_snapshot),
            previous_state=self._format_state(previous_state)
            if previous_state
            else "None",
            system_config=self.config,
        )
        try:
            should_halt, evaluation_from_evaluate_state = await self.quality_gate.evaluate_state(current_state_snapshot, previous_state)
            self.logger.debug(f"Evaluation object received from evaluate_state: {evaluation_from_evaluate_state} (Type: {type(evaluation_from_evaluate_state)})")

            # Create a new dictionary with all evaluation data, including state_snapshot and iteration
            evaluation = {
                **evaluation_from_evaluate_state,
                "state_snapshot": current_state_snapshot,
                "iteration": state['iteration_count'] + 1,
            }
            
            if state['iteration_count'] >= self.config.max_iterations:
                should_halt = True
            
            new_evals = state['quality_evaluations'] + [evaluation]
            
            log_node_execution(self.logger, "Quality Gate", {"current_state": current_state_snapshot},
                                 {"evaluation": evaluation}, time.time() - start_time)

            return {
                "should_halt": should_halt,
                "quality_evaluations": new_evals,
                "iteration_count": state['iteration_count'] + 1,
            }
        except Exception as e:
            self.logger.fatal(f"Error in quality gate: Type={type(e)}, Value={e}")
            return {"should_halt": True} # Halt on error

    async def human_approval_node(self, state: GraphState) -> Dict[str, Any]:
        self.logger.info("---Executing Human Approval Node---")
        if not self.config.enable_human_approval:
            self.logger.info("Human approval is disabled. Auto-approving.")
            return {"human_approval": True}

        self.logger.info("Waiting for human approval. Review the current state and type 'approve' or 'reject'.")
        self.logger.info(f"Current Design: {state['design']}")
        
        # In a real CLI, this would be an input() call. For async, we'll simulate.
        # For now, we'll auto-approve in the absence of actual human input.
        # In a real interactive system, this would block until user input.
        # For testing purposes, we'll assume approval.
        
        # TODO: Implement actual blocking input for CLI
        # For now, auto-approve
        self.logger.info("Auto-approving for demonstration purposes.")
        return {"human_approval": True}

    async def reflector_node(self, state: GraphState) -> Dict[str, Any]:
        self.logger.info("---Executing Reflector Node---")
        start_time = time.time()
        llm_config = self.llm_configs["reflector"]
        
        # Prepare context for the Reflector LLM
        evaluations_summary = "\n".join([str(eval) for eval in state['quality_evaluations']])
        prompt_parts = get_prompt("reflector", main_content=evaluations_summary, system_config=self.config, context=f"Iteration: {state['iteration_count']}")
        self.logger.debug(f"Prompt context for Reflector: Iteration: {state['iteration_count']}")
        messages = []
        if prompt_parts.get("system"):
            messages.append({"role": "system", "content": prompt_parts["system"]})
        messages.append({"role": "user", "content": prompt_parts["user"]})
        self.logger.debug(f"Messages sent to Reflector: {messages}")

        try:
            response = await self.llm_manager.generate_response(llm_config, messages)
            self.logger.debug(f"Raw response from Reflector (length {len(response)}): {response[:500]}...")
            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response, self.llm_configs["distiller"])
            
            updated_state = {
                'strategic_guidance': response,
            }
            log_node_execution(self.logger, "Reflector", {"quality_evaluations": evaluations_summary}, {"strategic_guidance": response}, time.time() - start_time)
        except ValueError as e:
            error_message = f"ERROR: LLM Model '{llm_config.model_id}' required for Reflector is not available. Please pull it using 'ollama pull {llm_config.model_id}'."
            self.logger.error(error_message)
            updated_state = {'strategic_guidance': error_message}
        except Exception as e:
            self.logger.fatal(f"Error in reflector node: {e}")
            updated_state = {'strategic_guidance': f"Error in reflector node: {e}"}
        return updated_state

    async def output_generation_node(self, state: GraphState) -> Dict[str, Any]:
        self.logger.info("---Executing Output Generation Node---")
        self.logger.info("🎉 WORKFLOW COMPLETED SUCCESSFULLY")
        return {}

    def _format_state(self, state_dict: Dict[str, Any]) -> str:
        """Formats a state dictionary into a human-readable string for prompts."""
        if not state_dict:
            return "No state available."
        formatted_parts = []
        for key, value in state_dict.items():
            # Truncate long values for readability in prompts
            if isinstance(value, str) and len(value) > 500:
                formatted_parts.append(f"{key}: {value[:500]}... (truncated)")
            else:
                formatted_parts.append(f"{key}: {value}")
        return "\n".join(formatted_parts)

    async def run(self, user_input: str):
        """
        Executes the compiled graph.
        """
        self.logger.info("🚀 STARTING GRAPH-BASED COOPERATIVE LLM WORKFLOW")
        initial_state = {
            "user_input": user_input,
            "iteration_count": 0,
            "should_halt": False,
            "requirements": "",
            "design": "",
            "code": "",
            "test_results": "",
            "review_feedback": "",
            "deliverables": {}, # Initialize empty
            "quality_evaluations": [],
            "strategic_guidance": "",
            "human_approval": False, # Initialize human_approval
        }
        
        # Execute the graph and get the final state
        recursion_limit = self.config.max_iterations * 10
        self.logger.debug(f"Setting graph recursion limit to: {recursion_limit}")
        final_state = await self.graph.ainvoke(initial_state, config={"recursion_limit": recursion_limit})

        self.logger.debug(f"Final state after graph execution: {final_state}")

        # After the graph run, populate the deliverables dictionary from the final state
        if final_state:
            final_state['deliverables'] = {
                'requirements': final_state.get('requirements', ''),
                'design': final_state.get('design', ''),
                'code': final_state.get('code', ''),
                'test_results': final_state.get('test_results', ''),
                'review_feedback': final_state.get('review_feedback', ''),
                'strategic_guidance': final_state.get('strategic_guidance', ''),
            }

        return final_state
