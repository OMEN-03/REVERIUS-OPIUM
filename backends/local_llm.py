from __future__ import annotations

import logging
from typing import Any

from .base import BackendResponse
from .errors import InitializationError

logger = logging.getLogger(__name__)


class LocalLLMBackend:
    """A local placeholder backend for environments without remote provider access."""

    name = "local_llm"
    priority = 20

    def __init__(self) -> None:
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("local llm backend initialized")

    async def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        if not self._initialized:
            await self.initialize()
        return BackendResponse(text=f"[local_llm] {prompt[:max_tokens]}", backend=self.name)

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        if not self._initialized:
            await self.initialize()
        return BackendResponse(text="[local_llm] ready", backend=self.name)

    async def stream(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256):
        if not self._initialized:
            await self.initialize()
        yield BackendResponse(text=f"[local_llm] {prompt[:max_tokens]}", backend=self.name)

    async def embeddings(self, text: str) -> list[float]:
        return [float(len(text)), 0.0]

    async def health_check(self) -> bool:
        return self._initialized

    async def shutdown(self) -> None:
        self._initialized = False
