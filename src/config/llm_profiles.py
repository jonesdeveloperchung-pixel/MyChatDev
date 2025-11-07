# config/llm_profiles.py
"""
Centralised definition of all LLM profiles.

Author: Jones Chung

Each profile is a mapping from role name → LLMConfig.
The dictionary `AVAILABLE_LLMS_BY_PROFILE` lets the CLI pick one
by its short key (e.g. "gemma3_phi4_gpt" or "llama32").
"""

from typing import Dict

# Import LLMConfig from its module (update the import path if needed)
from .settings import LLMConfig

# -------------------  Profile 1 – Mixed Gemma/phi4/GPT‑OSS -------------------
LLM_CONFIGS_GEMMA3_PHI4_GPT: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(
        name="Product Manager",
        model_id="gemma3:12b",
        role="product_manager",
        temperature=0.3,
    ),
    "architect": LLMConfig(
        name="System Architect",
        model_id="phi4:14b",
        role="architect",
        temperature=0.2,
    ),
    "programmer": LLMConfig(
        name="Programmer",
        model_id="gpt-oss:20b",
        role="programmer",
        temperature=0.1,
    ),
    "tester": LLMConfig(
        name="Tester",
        model_id="gemma3:4b",
        role="tester",
        temperature=0.2,
    ),
    "reviewer": LLMConfig(
        name="Code Reviewer",
        model_id="phi4:14b",
        role="reviewer",
        temperature=0.3,
    ),
    "reflector": LLMConfig(  # Added
        name="Reflector",
        model_id="gemma3:4b",
        role="reflector",
        temperature=0.2,
    ),
    "quality_gate": LLMConfig(  # Added
        name="Quality Gate",
        model_id="gemma3:4b",
        role="quality_gate",
        temperature=0.1,
    ),
}

# -------------------  Profile 2 – All GPT‑OSS --------------------------------
LLM_CONFIGS_GPT_OSS: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(
        name="Product Manager",
        model_id="gpt-oss:20b",
        role="product_manager",
        temperature=0.3,
    ),
    "architect": LLMConfig(
        name="System Architect",
        model_id="gpt-oss:20b",
        role="architect",
        temperature=0.2,
    ),
    "programmer": LLMConfig(
        name="Programmer",
        model_id="gpt-oss:20b",
        role="programmer",
        temperature=0.1,
    ),
    "tester": LLMConfig(
        name="Tester",
        model_id="gpt-oss:20b",
        role="tester",
        temperature=0.2,
    ),
    "reviewer": LLMConfig(
        name="Code Reviewer",
        model_id="gpt-oss:20b",
        role="reviewer",
        temperature=0.3,
    ),
    "distiller": LLMConfig(  # Added
        name="Distiller",
        model_id="gpt-oss:20b",
        role="distiller",
        temperature=0.2,
    ),
    "reflector": LLMConfig(  # Added
        name="Reflector",
        model_id="gpt-oss:20b",
        role="reflector",
        temperature=0.2,
    ),
    "quality_gate": LLMConfig(
        name="Quality Gate",
        model_id="gpt-oss:20b",
        role="quality_gate",
        temperature=0.1,
    ),
}

# -------------------  Profile 3 – All LLAMA3.2 --------------------------------
LLM_CONFIGS_LLAMMA32: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(
        name="Product Manager",
        model_id="llama3.2:3b",
        role="product_manager",
        temperature=0.3,
    ),
    "architect": LLMConfig(
        name="System Architect",
        model_id="llama3.2:3b",
        role="architect",
        temperature=0.2,
    ),
    "programmer": LLMConfig(
        name="Programmer",
        model_id="llama3.2:3b",
        role="programmer",
        temperature=0.1,
    ),
    "tester": LLMConfig(
        name="Tester",
        model_id="llama3.2:3b",
        role="tester",
        temperature=0.2,
    ),
    "reviewer": LLMConfig(
        name="Code Reviewer",
        model_id="llama3.2:3b",
        role="reviewer",
        temperature=0.3,
    ),
    "distiller": LLMConfig(  # Added
        name="Distiller",
        model_id="llama3.2:3b",
        role="distiller",
        temperature=0.2,
    ),
    "reflector": LLMConfig(  # Added
        name="Reflector",
        model_id="llama3.2:3b",
        role="reflector",
        temperature=0.2,
    ),
    "quality_gate": LLMConfig(  # Added
        name="Quality Gate",
        model_id="llama3.2:3b",
        role="quality_gate",
        temperature=0.1,
    ),

}

# -------------------  Profile 4 – Optimized (Copilot) --------------------------------
LLM_CONFIGS_HIGH_REASONING: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(
        name="Product Manager",
                model_id="gemma3:12b",  # balance of reasoning + efficiency
        role="product_manager",
        temperature=0.4,  # slightly higher for creativity
    ),
    "architect": LLMConfig(
        name="System Architect",
                model_id="phi4:14b",  # strong logical reasoning & planning
        role="architect",
        temperature=0.2,
    ),
    "programmer": LLMConfig(
        name="Programmer",
                model_id="qwen2.5-coder:latest",  # A strong coding model from your list
        role="programmer",
        temperature=0.1,
    ),
    "tester": LLMConfig(
        name="Tester",
                model_id=(
            "deepseek-coder:6.7b"
        ),  # A coding model to generate relevant tests
        role="tester",
        temperature=0.25,
    ),
    "reviewer": LLMConfig(
        name="Code Reviewer",
                model_id="gemma3:4b",  # smaller but precise, good for review
        role="reviewer",
        temperature=0.2,
    ),
    "distiller": LLMConfig(
        name="Distiller",
                model_id="gemma3:1b",  # Your smallest model for summarization
        role="distiller",
        temperature=0.2,
    ),
    "reflector": LLMConfig(
        name="Reflector",
                model_id="phi4:14b",  # A powerful model for root cause analysis
        role="reflector",
        temperature=0.2,
    ),
    "quality_gate": LLMConfig(
        name="Quality Gate",
                model_id=(
            "gemma3:4b"
        ),  # A reliable model for scoring and classification
        role="quality_gate",
        temperature=0.1,
    ),
}

# -------------------  Profile 5 – Lightweight (Copilot) --------------------------------
LLM_CONFIGS_LIGHTWEIGHT: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(
        name="Product Manager",
        model_id="gemma3:4b",  # Replaced llama3.2:3b (1.9GB) with gemma3:4b (3.1GB)
        role="product_manager",
        temperature=0.4,
    ),
    "architect": LLMConfig(
        name="System Architect",
        model_id="gemma3:4b",  # Replaced llama3.2:3b (1.9GB) with gemma3:4b (3.1GB)
        role="architect",
        temperature=0.2,
    ),
    "programmer": LLMConfig(
        name="Programmer",
        model_id="deepseek-coder:6.7b",  # Already >3GB
        role="programmer",
        temperature=0.1,
    ),
    "tester": LLMConfig(
        name="Tester",
        model_id="neural-chat:latest",  # Replaced tinyllama:latest (608MB) with neural-chat:latest (3.9GB)
        role="tester",
        temperature=0.2,
    ),
    "reviewer": LLMConfig(
        name="Code Reviewer",
        model_id="neural-chat:latest", # Already >3GB
        role="reviewer",
        temperature=0.3,
    ),
    "distiller": LLMConfig( # Added
        name="Distiller",
        model_id="gemma3:4b", # Replaced tinyllama:latest (608MB) with gemma3:4b (3.1GB)
        role="distiller",
        temperature=0.2,
    ),
    "reflector": LLMConfig(  # Added
        name="Reflector",
        model_id="neural-chat:latest",  # Replaced tinyllama:latest (608MB) with neural-chat:latest (3.9GB)
        role="reflector",
        temperature=0.2,
    ),
    "quality_gate": LLMConfig( # Added
        name="Quality Gate",
        model_id="gemma3:4b", # Replaced tinyllama:latest (608MB) with gemma3:4b (3.1GB)
        role="quality_gate",
        temperature=0.1,
    ),
}

# -------------------  Profile 8 – Medium Reasoning ---------------------------------------
LLM_CONFIGS_MEDIUM_REASONING: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(
        name="Product Manager",
        model_id="llama3.2:3b",
        role="product_manager",
        temperature=0.4,
    ),
    "architect": LLMConfig(
        name="System Architect",
        model_id="llama3.2:3b",
        role="architect",
        temperature=0.2,
    ),
    "programmer": LLMConfig(
        name="Programmer",
        model_id="deepseek-coder:6.7b",
        role="programmer",
        temperature=0.1,
    ),
    "tester": LLMConfig(
        name="Tester",
        model_id="gemma3:4b", # Upgraded from tinyllama
        role="tester",
        temperature=0.2,
    ),
    "reviewer": LLMConfig(
        name="Code Reviewer",
        model_id="neural-chat:latest",
        role="reviewer",
        temperature=0.3,
    ),
    "distiller": LLMConfig(
        name="Distiller",
        model_id="tinyllama:latest",  # Smallest for summarization
        role="distiller",
        temperature=0.2,
    ),
    "reflector": LLMConfig(
        name="Reflector",
        model_id="llama3.2:3b",  # Good for analysis
        role="reflector",
        temperature=0.2,
    ),
    "quality_gate": LLMConfig(
        name="Quality Gate",
        model_id="gemma3:4b", # Reliable for scoring
        role="quality_gate",
        temperature=0.1,
    ),
}

# -------------------  Profile 6 – Compliance (Copilot) ---------------------------------------
LLM_CONFIGS_COMPLIANCE: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(
        name="Product Manager",
        model_id="gpt-oss:20b",  # Strategic generalist
        role="product_manager",
        temperature=0.3,
    ),
    "architect": LLMConfig(
        name="System Architect",
        model_id="phi4:14b",  # Reasoning-heavy, ideal for architecture
        role="architect",
        temperature=0.2,
    ),
    "programmer": LLMConfig(
        name="Programmer",
        model_id="codegemma:latest",  # Code-specialized
        role="programmer",
        temperature=0.1,
    ),
    "tester": LLMConfig(
        name="Tester",
        model_id="gemma3:12b",  # Strong reasoning for edge case detection
        role="tester",
        temperature=0.2,
    ),
    "reviewer": LLMConfig(
        name="Code Reviewer",
        model_id="llama3.2:latest",  # Balanced generalist with good comprehension
        role="reviewer",
        temperature=0.3,
    ),
    "distiller": LLMConfig(
        name="Distiller",
        model_id="mistral:7b",  # Lightweight summarization and synthesis
        role="distiller",
        temperature=0.2,
    ),
    "reflector": LLMConfig(
        name="Reflector",
        model_id="phi3:latest",  # Compact model for introspection and reflection
        role="reflector",
        temperature=0.2,
    ),
    "quality_gate": LLMConfig(
        name="Quality Gate",
        model_id="gemma3n:e4b",  # Efficient evaluator with enhanced reasoning
        role="quality_gate",
        temperature=0.1,
    ),
}

# -------------------  Profile 7 – Low Reasoning (formerly Fast) ---------------------------------------
LLM_CONFIGS_LOW_REASONING: Dict[str, LLMConfig] = {
    "product_manager": LLMConfig(
        name="Product Manager",
        model_id="tinyllama:latest",
        role="product_manager",
        temperature=0.3,
    ),
    "architect": LLMConfig(
        name="System Architect",
        model_id="tinyllama:latest",
        role="architect",
        temperature=0.2,
    ),
    "programmer": LLMConfig(
        name="Programmer",
        model_id="deepseek-coder:1.3b",
        role="programmer",
        temperature=0.1,
    ),
    "tester": LLMConfig(
        name="Tester",
        model_id="tinyllama:latest",
        role="tester",
        temperature=0.2,
    ),
    "reviewer": LLMConfig(
        name="Code Reviewer",
        model_id="tinyllama:latest",
        role="reviewer",
        temperature=0.3,
    ),
    "distiller": LLMConfig(
        name="Distiller",
        model_id="tinyllama:latest",
        role="distiller",
        temperature=0.2,
    ),
    "reflector": LLMConfig(
        name="Reflector",
        model_id="tinyllama:latest",
        role="reflector",
        temperature=0.2,
    ),
    "quality_gate": LLMConfig(
        name="Quality Gate",
        model_id="gemma3:4b",
        role="quality_gate",
        temperature=0.1,
    ),
}

# -------------------  Public mapping -----------------------------------------
AVAILABLE_LLMS_BY_PROFILE: Dict[str, Dict[str, LLMConfig]] = {
    "Advanced_Hybrid": LLM_CONFIGS_GEMMA3_PHI4_GPT,
    "OpenSource_General": LLM_CONFIGS_GPT_OSS,
    "Llama_Specialized": LLM_CONFIGS_LLAMMA32,
    "High_Reasoning": LLM_CONFIGS_HIGH_REASONING,  # Default profile
    "Medium_Reasoning": LLM_CONFIGS_MEDIUM_REASONING,
    "Low_Reasoning": LLM_CONFIGS_LOW_REASONING,
    "Fast_Lightweight": LLM_CONFIGS_LIGHTWEIGHT,
    "Compliance_Focused": LLM_CONFIGS_COMPLIANCE,
}
