"""BlackBox — AI Models & Diagnostics API Router."""
from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ai.provider import NebiusAIProvider
from app.config import get_settings

router = APIRouter(prefix="/ai", tags=["ai"])


class AIModelItem(BaseModel):
    id: str
    name: str
    tag: str
    tier: str
    description: str
    context_window: str
    recommended: bool


class TestLLMRequest(BaseModel):
    model: Optional[str] = Field(None, description="Model ID to test")


class TestLLMResponse(BaseModel):
    status: str
    configured: bool
    latency_ms: Optional[float] = None
    model: str
    message: str
    reply: Optional[str] = None


# Curated premier NVIDIA & open models actively verified on Nebius Token Factory
CURATED_MODELS: List[AIModelItem] = [
    AIModelItem(
        id="nvidia/Nemotron-3-Ultra-550b-a55b",
        name="NVIDIA Nemotron 3 Ultra 550B",
        tag="NVIDIA Flagship",
        tier="High Accuracy & Reasoning",
        description="Premier NVIDIA open model on Nebius. Massive 550B architecture for deep architectural analysis, complex call tracing, and unified diff patches.",
        context_window="128K",
        recommended=True,
    ),
    AIModelItem(
        id="nvidia/Nemotron-3_5-Lightning",
        name="NVIDIA Nemotron 3.5 Lightning",
        tag="NVIDIA Fast",
        tier="Ultra Low Latency",
        description="High-speed NVIDIA inference (~580ms latency). Ideal for fast repository exploration and lightweight Q&A.",
        context_window="64K",
        recommended=False,
    ),
    AIModelItem(
        id="Qwen/Qwen3-30B-A3B-Instruct-2507",
        name="Qwen 3 30B Instruct (MoE)",
        tag="Code Specialist",
        tier="Coding Pro",
        description="Advanced Mixture-of-Experts coding model with benchmark-topping syntax comprehension and multi-file debugging.",
        context_window="128K",
        recommended=False,
    ),
    AIModelItem(
        id="Qwen/Qwen3.8-27B",
        name="Qwen 3.8 27B Instruct",
        tag="Compact",
        tier="Fast & Efficient",
        description="Highly optimized 27B parameter coding engine with sub-second latency and minimal token consumption.",
        context_window="32K",
        recommended=False,
    ),
    AIModelItem(
        id="google/gemma-3-27b-it",
        name="Google Gemma 3 27B Instruct",
        tag="Balanced",
        tier="Instruction Tuned",
        description="Google open-weights model fine-tuned for structured instruction following and architectural analysis.",
        context_window="128K",
        recommended=False,
    ),
    AIModelItem(
        id="moonshotai/Kimi-K2.7-Code",
        name="Moonshot Kimi K2.7 Code",
        tag="Code Expert",
        tier="Deep Code Analysis",
        description="Specialized coding model trained specifically on massive software repositories and architectural patterns.",
        context_window="128K",
        recommended=False,
    ),
]


@router.get("/models", response_model=List[AIModelItem], summary="List curated available LLMs")
async def list_ai_models() -> List[AIModelItem]:
    """Return active curated list of premier NVIDIA / open models without deprecated options."""
    return CURATED_MODELS


@router.post("/test", response_model=TestLLMResponse, summary="Test LLM connection and measure latency")
async def test_llm_connection(req: Optional[TestLLMRequest] = None) -> TestLLMResponse:
    """Send a lightweight ping to verify API key validity, model readiness, and response latency."""
    selected_model = req.model if req and req.model else None
    provider = NebiusAIProvider(model=selected_model)
    result = await provider.test_connection(model=selected_model)
    return TestLLMResponse.model_validate(result)
