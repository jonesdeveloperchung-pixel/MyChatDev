"""Simplified workflow implementation without LangGraph dependencies."""

import time
import logging
from typing import Dict, Any
from models.llm_manager import LLMManager
from workflow.quality_gate import QualityGate
from config.settings import AVAILABLE_LLMS, DEFAULT_CONFIG
from utils.prompts import get_prompt
from utils.logging_config import log_node_execution


class WorkflowState:
    """State management for the workflow."""
    
    def __init__(self):
        self.user_input: str = ""
        self.requirements: str = ""
        self.design: str = ""
        self.code: str = ""
        self.test_results: str = ""
        self.review_feedback: str = ""
        self.deliverables: Dict[str, str] = {}
        self.iteration_count: int = 0
        self.quality_evaluations: list = []
        self.should_halt: bool = False


class SimpleCooperativeLLM:
    """Simple implementation of cooperative LLM workflow."""
    
    def __init__(self, config=DEFAULT_CONFIG, llm_configs=None):
        """Initialize the workflow."""
        self.config = config
        self.llm_manager = LLMManager(config)
        self.quality_gate = QualityGate(
            self.llm_manager, 
            config.quality_threshold, 
            config.change_threshold
        )
        self.logger = logging.getLogger("coop_llm.simple")
        # Use provided LLM configs or fall back to default
        self.llm_configs = llm_configs or AVAILABLE_LLMS
    
    async def requirements_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Product Manager analyzes requirements."""
        start_time = time.time()
        
        llm_config = self.llm_configs["product_manager"]
        prompt = get_prompt(
            "product_manager",
            user_input=state.user_input,
            context=f"Iteration: {state.iteration_count}"
        )
        
        try:
            response = await self.llm_manager.generate_response(llm_config, prompt)
            
            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response)
            
            state.requirements = response
            state.deliverables["requirements"] = response
            
            execution_time = time.time() - start_time
            log_node_execution(
                self.logger, "Requirements Analysis",
                {"user_input": state.user_input},
                {"requirements": response},
                execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in requirements analysis: {e}")
            state.requirements = f"Error in requirements analysis: {e}"
        
        return state
    
    async def system_design_node(self, state: WorkflowState) -> WorkflowState:
        """Architect designs the system."""
        start_time = time.time()
        
        llm_config = self.llm_configs["architect"]
        prompt = get_prompt(
            "architect",
            requirements=state.requirements,
            context=f"Iteration: {state.iteration_count}"
        )
        
        try:
            response = await self.llm_manager.generate_response(llm_config, prompt)
            
            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response)
            
            state.design = response
            state.deliverables["design"] = response
            
            execution_time = time.time() - start_time
            log_node_execution(
                self.logger, "System Design",
                {"requirements": state.requirements},
                {"design": response},
                execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in system design: {e}")
            state.design = f"Error in system design: {e}"
        
        return state
    
    async def code_implementation_node(self, state: WorkflowState) -> WorkflowState:
        """Programmer implements the code."""
        start_time = time.time()
        
        llm_config = self.llm_configs["programmer"]
        prompt = get_prompt(
            "programmer",
            design=state.design,
            context=f"Iteration: {state.iteration_count}"
        )
        
        try:
            response = await self.llm_manager.generate_response(llm_config, prompt)
            
            if self.config.enable_compression and len(response) > self.config.compression_threshold:
                response = await self.llm_manager.compress_content(response)
            
            state.code = response
            state.deliverables["code"] = response
            
            execution_time = time.time() - start_time
            log_node_execution(
                self.logger, "Code Implementation",
                {"design": state.design},
                {"code": response},
                execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in code implementation: {e}")
            state.code = f"Error in code implementation: {e}"
        
        return state
    
    async def testing_debugging_node(self, state: WorkflowState) -> WorkflowState:
        """Tester validates the implementation."""
        start_time = time.time()
        
        llm_config = self.llm_configs["tester"]
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
            
            state.test_results = response
            state.deliverables["test_results"] = response
            
            execution_time = time.time() - start_time
            log_node_execution(
                self.logger, "Testing & Debugging",
                {"code": state.code, "requirements": state.requirements},
                {"test_results": response},
                execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in testing: {e}")
            state.test_results = f"Error in testing: {e}"
        
        return state
    
    async def review_refinement_node(self, state: WorkflowState) -> WorkflowState:
        """Reviewer provides feedback and refinement."""
        start_time = time.time()
        
        llm_config = self.llm_configs["reviewer"]
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
            
            state.review_feedback = response
            state.deliverables["review_feedback"] = response
            
            execution_time = time.time() - start_time
            log_node_execution(
                self.logger, "Review & Refinement",
                {"deliverables": deliverables_text},
                {"review_feedback": response},
                execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in review: {e}")
            state.review_feedback = f"Error in review: {e}"
        
        return state
    
    async def quality_gate_node(self, state: WorkflowState) -> WorkflowState:
        """Quality gate evaluation."""
        start_time = time.time()
        
        # Get previous state for comparison
        previous_state = None
        if state.quality_evaluations:
            previous_state = state.quality_evaluations[-1].get("state_snapshot")
        
        # Current state snapshot
        current_state_snapshot = {
            "requirements": state.requirements,
            "design": state.design,
            "code": state.code,
            "test_results": state.test_results,
            "review_feedback": state.review_feedback
        }
        
        try:
            should_halt, evaluation = await self.quality_gate.evaluate_state(
                current_state_snapshot, previous_state
            )
            
            state.should_halt = should_halt
            state.iteration_count += 1
            
            # Store evaluation
            evaluation["state_snapshot"] = current_state_snapshot
            evaluation["iteration"] = state.iteration_count
            state.quality_evaluations.append(evaluation)
            
            execution_time = time.time() - start_time
            log_node_execution(
                self.logger, "Quality Gate",
                {"current_state": current_state_snapshot},
                {"evaluation": evaluation},
                execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in quality gate: {e}")
            state.should_halt = state.iteration_count >= self.config.max_iterations
        
        return state
    
    async def output_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Generate final outputs and deliverables."""
        start_time = time.time()
        
        # Compile final deliverables
        final_deliverables = {
            "requirements_specification": state.requirements,
            "system_design": state.design,
            "source_code": state.code,
            "test_results": state.test_results,
            "review_feedback": state.review_feedback,
            "quality_evaluations": state.quality_evaluations,
            "iteration_count": state.iteration_count
        }
        
        state.deliverables.update(final_deliverables)
        
        execution_time = time.time() - start_time
        log_node_execution(
            self.logger, "Output Generation",
            {"iteration_count": state.iteration_count},
            {"final_deliverables": list(final_deliverables.keys())},
            execution_time
        )
        
        self.logger.info("🎉 WORKFLOW COMPLETED SUCCESSFULLY")
        return state
    
    async def run(self, user_input: str) -> WorkflowState:
        """Execute the complete workflow."""
        self.logger.info("🚀 STARTING COOPERATIVE LLM WORKFLOW")
        
        # Initialize state
        state = WorkflowState()
        state.user_input = user_input
        
        try:
            # Execute workflow nodes in sequence
            while not state.should_halt and state.iteration_count < self.config.max_iterations:
                # Run workflow steps
                state = await self.requirements_analysis_node(state)
                state = await self.system_design_node(state)
                state = await self.code_implementation_node(state)
                state = await self.testing_debugging_node(state)
                state = await self.review_refinement_node(state)
                state = await self.quality_gate_node(state)
                
                # Force at least 2 iterations if quality is low
                if state.should_halt:
                    if state.iteration_count < 2 and len(state.quality_evaluations) > 0:
                        last_quality = state.quality_evaluations[-1].get("quality_score", 0)
                        if last_quality < self.config.quality_threshold:
                            self.logger.info(f"🔄 Quality {last_quality:.2f} < {self.config.quality_threshold}, forcing iteration {state.iteration_count + 1}")
                            state.should_halt = False
                            continue
                    break
            
            # Generate final output
            state = await self.output_generation_node(state)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in workflow execution: {e}")
            raise