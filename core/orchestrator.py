from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backends.backend_manager import BackendManager
from core.architecture import evaluate_user_request, get_ethical_foundation_prompt

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineResult:
    """Represents the output of a single AI pipeline run."""

    intent: str
    plan: list[str] = field(default_factory=list)
    response: str = ""
    reflection: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class AIOrchestrator:
    """Coordinates intent detection, planning, execution, and reflection."""

    def __init__(self, backend_manager: BackendManager | None = None) -> None:
        self.backend_manager = backend_manager or BackendManager()
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        await self.backend_manager.initialize()
        self._initialized = True

    async def handle_request(self, request: str) -> PipelineResult:
        """Process a request through the full pipeline."""
        if not self._initialized:
            await self.initialize()

        ethical_review = evaluate_user_request(request)
        if not ethical_review.allowed:
            return PipelineResult(
                intent="blocked",
                plan=["reject request"],
                response=ethical_review.reason or "Request blocked.",
                reflection="reflection: request rejected due to ethical policy",
                metadata={"ethical_review": ethical_review.__dict__},
            )

        intent = self._classify_intent(request)
        plan = self._build_plan(request, intent)
        response = await self._execute_plan(request, plan)
        reflection = self._reflect(response, plan, intent)
        return PipelineResult(intent=intent, plan=plan, response=response, reflection=reflection)

    def _classify_intent(self, request: str) -> str:
        text = request.lower()
        if any(keyword in text for keyword in ("code", "python", "function", "script")):
            return "coding"
        if any(keyword in text for keyword in ("plan", "task", "project", "strategy")):
            return "planning"
        if any(keyword in text for keyword in ("voice", "speak", "audio")):
            return "voice"
        if any(keyword in text for keyword in ("image", "vision", "photo", "screen")):
            return "vision"
        return "general"

    def _build_plan(self, request: str, intent: str) -> list[str]:
        base = [
            "understand the request",
            "retrieve relevant memory context",
            "select the appropriate tool or backend",
            "generate a response",
        ]
        if intent == "coding":
            return base + ["verify the proposed solution"]
        if intent == "planning":
            return base + ["structure the plan into actionable steps"]
        return base + ["review the response for quality"]

    async def _execute_plan(self, request: str, plan: list[str]) -> str:
        backend_response = await self.backend_manager.generate(
            f"{get_ethical_foundation_prompt()}\n\nRequest: {request}\n\nPlan: {', '.join(plan)}",
            temperature=0.2,
            max_tokens=256,
        )
        return backend_response.text

    def _reflect(self, response: str, plan: list[str], intent: str) -> str:
        return (
            f"reflection: handled {intent} request with plan {', '.join(plan)}; "
            f"response length={len(response)}"
        )
