# test_quality_gate.py
import asyncio
import json
from pathlib import Path
import pytest

from quality_gate import QualityGate, QualityResult
from models.llm_manager import LLMManager
from config.settings import LLMConfig
from unittest.mock import AsyncMock

@pytest.fixture
def fake_llm_manager():
    mgr = LLMManager()
    mgr.generate_response = AsyncMock(return_value=json.dumps({
        "quality_score": 0.92,
        "change_magnitude": 0.04,
        "confidence": 0.97,
        "decision": "HALT"
    }))
    return mgr

@pytest.mark.asyncio
async def test_gate_halts_on_high_quality(fake_llm_manager):
    gate = QualityGate(
        llm_manager=fake_llm_manager,
        gate_config=LLMConfig(name="Gate", model_id="gemma3:12b", role="quality_gate"),
        quality_threshold=0.9,
        change_threshold=0.1,
    )
    should, result = await gate.evaluate({"code": "x"}, {"code": "x"})
    assert should is True
    assert isinstance(result, QualityResult)
    assert result.quality_score == 0.92