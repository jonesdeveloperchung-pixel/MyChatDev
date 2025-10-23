"""
Quality gate implementation for controlling workflow execution.
The gate decides whether the current iteration of the cooperative‑LLM
workflow should continue or be stopped based on a short LLM‑generated
assessment of the workflow state.

Author: Jones Chung
"""

import logging
import re
import json # Add this import
from typing import Dict, Any, Tuple

from models.llm_manager import LLMManager
from config.settings import LLMConfig
from utils.prompts import get_prompt


class QualityGate:
    """
    A lightweight “watch‑dog” that interrogates the workflow’s
    current snapshot (requirements, design, code, tests, review feedback,
    …) and decides whether to halt or keep iterating.

    How it works
    -------------
    1. A prompt is built from the current and, if available, the previous
       snapshot and sent to a *dedicated* LLM (`gemma3:12b`).
    2. The LLM returns a short text containing a quality score, a change
       magnitude, a decision flag, and optional reasoning.
    3. Those four values are parsed, logged, and used to compute
       `should_halt`.
    4. The decision is returned to the caller along with a dictionary of
       the raw metrics so that the rest of the system can log or store
       them.
    """

    def __init__(
        self,
        llm_manager: LLMManager,
        gate_config: LLMConfig,
        quality_threshold: float = 0.8,
        change_threshold: float = 0.1,
    ):
        """
        Initialise the quality gate.

        Parameters
        ----------
        llm_manager : LLMManager
            Object that knows how to call the LLM API (wrapper around
            OpenAI/Ollama/…).
        gate_config : LLMConfig
            The specific LLM configuration for the quality gate agent.
        quality_threshold : float, optional
            If the LLM’s quality score ≥ this value the gate will halt.
            Default: 0.8.
        change_threshold : float, optional
            If the LLM reports that the change between this and the
            previous iteration is ≤ this value the gate will halt.
            Default: 0.1.
        """
        self.llm_manager = llm_manager
        self.gate_config = gate_config
        self.quality_threshold = quality_threshold
        self.change_threshold = change_threshold
        self.logger = logging.getLogger("coop_llm.quality_gate")

    def _should_halt(
        self,
        decision: str,
        quality: float,
        change: float,
        q_threshold: float,
        c_threshold: float,
    ) -> bool:
        """Return True if the workflow should stop."""
        if quality >= q_threshold and decision.upper() == "HALT":
            return True
        
        # Rule: If change is minimal, it might indicate stagnation, which should also halt
        if change <= c_threshold:
            return True

        # Otherwise, continue
        return False

    async def evaluate_state(
        self,
        current_state: Dict[str, Any],
        previous_state: Dict[str, Any] | None = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate the workflow’s current state and decide whether to continue
        or stop the next iteration.

        The method performs these steps:

        1. Build a prompt that includes a formatted view of the
           current state (and the previous state if present).
        2. Ask the LLM for an assessment.
        3. Parse the raw text into `quality_score`, `change_magnitude`,
           `decision` and `reasoning`.
        4. Log the metrics for observability.
        5. Compute `should_halt` based on the thresholds and the
           LLM’s decision.
        6. Return a tuple ``(should_halt, evaluation_result)`` where
           ``evaluation_result`` contains all parsed values and the raw
           assessment text.

        Parameters
        ----------
        current_state : dict
            Dictionary with the latest workflow snapshot.
        previous_state : dict | None, optional
            Snapshot from the previous iteration, if any.

        Returns
        -------
        Tuple[bool, dict]
            * ``should_halt`` – whether the workflow should stop.
            * ``evaluation_result`` – dictionary with metrics, decision,
              reasoning, and the raw assessment string.
        """
        self.logger.info("=== QUALITY GATE EVALUATION ===")

        # 1️⃣ Build the prompt that asks the LLM to assess the
        #     current / previous state.
        prompt_parts = get_prompt(
            "quality_gate",
            current_state=self._format_state(current_state),
            previous_state=self._format_state(previous_state)
            if previous_state
            else "None",
        )
        messages = []
        if prompt_parts.get("system"):
            messages.append({"role": "system", "content": prompt_parts["system"]})
        messages.append({"role": "user", "content": prompt_parts["user"]})

        self.logger.debug(f"Full prompt sent to Quality Gate LLM:\nSystem: {prompt_parts.get("system")}\nUser: {prompt_parts["user"]}\n---")

        try:
            # 2️⃣ Ask the LLM for a quality assessment.
            assessment = await self.llm_manager.generate_response(
                self.gate_config, messages
            )

            try:
                # 3️⃣ Parse the raw text into individual metrics.
                (
                    quality_score,
                    change_magnitude,
                    decision,
                    reasoning,
                ) = self._parse_assessment(assessment)
            except Exception as parse_e:
                self.logger.error(f"Error during _parse_assessment: {parse_e}")
                raise # Re-raise to be caught by the outer try-except

            # 4️⃣ Log the extracted metrics – useful for debugging.
            self.logger.info(f"Quality Score: {quality_score}")
            self.logger.info(f"Change Magnitude: {change_magnitude}")
            self.logger.info(f"Decision: {decision}")
            self.logger.info(f"Reasoning: {reasoning}")

            try:
                # 5️⃣ Determine whether to halt.
                should_halt = self._should_halt(
                    decision,
                    quality_score,
                    change_magnitude,
                    self.quality_threshold,
                    self.change_threshold,
                )
            except Exception as halt_e:
                self.logger.error(f"Error during _should_halt: {halt_e}")
                raise # Re-raise to be caught by the outer try-except

            evaluation_result = {
                "quality_score": quality_score,
                "change_magnitude": change_magnitude,
                "decision": decision,
                "reasoning": reasoning,
                "should_halt": should_halt,
                "assessment_text": assessment,
            }

            # 6️⃣ Log a concise summary of the outcome.
            if should_halt:
                self.logger.info("🛑 QUALITY GATE: HALTING EXECUTION")
                if quality_score >= self.quality_threshold:
                    self.logger.info(
                        f"✅ Quality threshold met: {quality_score} >= {self.quality_threshold}"
                    )
                if change_magnitude <= self.change_threshold:
                    self.logger.info(
                        f"📉 Minimal change detected: {change_magnitude} <= {self.change_threshold}"
                    )
            else:
                self.logger.info("🟢 QUALITY GATE: CONTINUING EXECUTION")

            self.logger.debug(f"evaluate_state returning: should_halt={should_halt}, evaluation_result={evaluation_result}")
            return should_halt, evaluation_result

        except Exception as e:
            self.logger.error(f"Error in quality gate evaluation: {e}")
            error_result = {
                "quality_score": 0.0,
                "change_magnitude": 1.0,
                "decision": "CONTINUE",
                "reasoning": f"Error in evaluation: {e}",
                "should_halt": False,
                "assessment_text": "",
            }
            self.logger.debug(f"evaluate_state returning (on error): should_halt={False}, evaluation_result={error_result}")
            return False, error_result

    def _format_state(self, state: Dict[str, Any] | None) -> str:
        """
        Convert a state dictionary into a human‑readable string for the LLM.

        Note: The content is no longer truncated here. It is expected that
        the input to this function has been intelligently compressed beforehand
        if necessary.
        """
        if not state:
            return "No state available"

        formatted_parts = []
        for key, value in state.items():
            formatted_parts.append(f"{key}: {str(value)}")

        return "\n".join(formatted_parts)

    def _parse_assessment(self, assessment: str) -> Tuple[float, float, str, str]:
        """
        Parse the LLM’s assessment text to extract numeric metrics.

        The LLM is expected to produce a short summary that looks roughly like:
        ```
        quality score: 0.92
        change magnitude: 0.03
        decision: HALT
        reasoning: Because the code changes are minimal...
        ```

        The parser uses regular expressions to pull out the four fields.
        If the format is unexpected, default values are returned.

        Returns
        -------
        Tuple[float, float, str, str]
            * quality_score
            * change_magnitude
            * decision
            * reasoning
        """
        # Default values if parsing fails.
        quality_score = 0.5
        change_magnitude = 0.5
        decision = "CONTINUE"
        reasoning = "Unable to parse assessment"

        self.logger.debug(f"Raw assessment from LLM: {assessment}")
        extracted_json_string = ""

        # 1. Try to extract JSON from a markdown code block (```json ... ```)
        json_match = re.search(r"```json\n(.*?)```", assessment, re.DOTALL)
        if json_match:
            extracted_json_string = json_match.group(1).strip()
            self.logger.debug(f"Extracted JSON from markdown block: {extracted_json_string}")
        else:
            # 2. If no markdown block, try to find the first and last curly brace
            #    to isolate a potential JSON object that's not wrapped.
            first_brace = assessment.find('{')
            last_brace = assessment.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                extracted_json_string = assessment[first_brace : last_brace + 1].strip()
                self.logger.debug(f"Extracted JSON by braces: {extracted_json_string}")
            else:
                self.logger.debug("No JSON markdown block or valid braces found. Proceeding with raw string for regex fallback.")
                extracted_json_string = assessment # Use the whole assessment for regex if no JSON found

        try:
            # Attempt to parse as JSON first
            json_assessment = json.loads(extracted_json_string)
            quality_score = float(json_assessment.get("quality_score", 0.5))
            change_magnitude = float(json_assessment.get("change_magnitude", 0.5))
            decision = json_assessment.get("decision", "CONTINUE").upper()
            reasoning = json_assessment.get("reasoning", "No reasoning provided.")

            # Normalise if the model accidentally returns >1 (e.g. “9.2”).
            if quality_score > 1:
                quality_score = quality_score / 10 if quality_score <= 10 else 1.0
            if change_magnitude > 1:
                change_magnitude = change_magnitude / 10 if change_magnitude <= 10 else 1.0

        except json.JSONDecodeError:
            self.logger.warning("LLM assessment is not valid JSON. Attempting regex parsing.")
            # Fallback to regex parsing if JSON parsing fails (for robustness)
            # Default values if parsing fails.
            quality_score = 0.5
            change_magnitude = 0.5
            decision = "CONTINUE"
            reasoning = "Unable to parse assessment"

            # ---------- Quality score ----------
            quality_match = re.search(
                r"quality.*?score.*?[:\-]?\s*([0-9]*\.?[0-9]+)",
                assessment,
                re.IGNORECASE,
            )
            if quality_match:
                quality_score = float(quality_match.group(1))
                # Normalise if the model accidentally returns >1 (e.g. “9.2”).
                if quality_score > 1:
                    quality_score = quality_score / 10 if quality_score <= 10 else 1.0

            # ---------- Change magnitude ----------
            change_match = re.search(
                r"change.*?magnitude.*?[:\-]?\s*([0-9]*\.?[0-9]+)",
                assessment,
                re.IGNORECASE,
            )
            if change_match:
                change_magnitude = float(change_match.group(1))
                if change_magnitude > 1:
                    change_magnitude = (
                        change_magnitude / 10 if change_magnitude <= 10 else 1.0
                    )

            # ---------- Decision ----------
            # Map common synonyms to a canonical “HALT” or “CONTINUE”.
            if re.search(r"\b(HALT|STOP|COMPLETE)\b", assessment, re.IGNORECASE):
                decision = "HALT"
            elif re.search(r"\b(CONTINUE|PROCEED)\b", assessment, re.IGNORECASE):
                decision = "CONTINUE"

            # ---------- Reasoning ----------
            # Find the first occurrence of a keyword followed by a colon/dash
            # and capture the rest of the line (or multiline).
            reasoning_patterns = [
                r"Reasoning[:\-]?\s*(.+)",  # Capture everything after "Reasoning:"
                r'reasoning"\s*:\s*"([^"]+)',  # Capture reasoning from JSON-like string if regex is used
                r"because[:\-]?\s*(.+?)(?:\n|$)",
                r"decision[:\-]?\s*(.+?)(?:\n|$)",
            ]
            for pattern in reasoning_patterns:
                reasoning_match = re.search(
                    pattern, assessment, re.IGNORECASE | re.DOTALL
                )
                if reasoning_match:
                    reasoning = reasoning_match.group(1).strip()
                    break
        except Exception as e:
            # Log the error but still return the defaults so the caller can
            # decide to continue.
            self.logger.error(f"Error parsing assessment: {e}")

        return quality_score, change_magnitude, decision, reasoning
