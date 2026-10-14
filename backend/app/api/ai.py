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


# Curated premier NVIDIA & open models available on Nebius Token Factory
CURATED_MODELS: List[AIModelItem] = [
    AIModelItem(
        id="meta-llama/Meta-Llama-3.1-70B-Instruct",
        name="Llama 3.1 70B Instruct",
        tag="Flagship",
        tier="High Accuracy",
        description="NVIDIA premier open model. Best for deep architectural analysis, complex call tracing, and unified diff patches.",
        context_window="128K",
        recommended=True,
    ),
    AIModelItem(
        id="meta-llama/Meta-Llama-3.1-8B-Instruct",
        name="Llama 3.1 8B Instruct",
        tag="Ultra Fast",
        tier="Lightweight & Fast",
        description="Lightning fast inference and minimal token consumption. Ideal for quick questions and budget-friendly tiers.",
        context_window="128K",
        recommended=False,
    ),
    AIModelItem(
        id="Qwen/Qwen2.5-Coder-32B-Instruct",
        name="Qwen 2.5 Coder 32B",
        tag="Code Specialist",
        tier="Coding Pro",
        description="Benchmark-topping code comprehension. Specialized in multi-language AST synthesis and deep logic debugging.",
        context_window="32K",
        recommended=False,
    ),
    AIModelItem(
        id="mistralai/Mistral-7B-Instruct-v0.3",
        name="Mistral 7B Instruct v0.3",
        tag="Compact",
        tier="Low Latency",
        description="High token efficiency with concise technical explanations and reliable function calls.",
        context_window="32K",
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
