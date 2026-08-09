from __future__ import annotations

import logging

from .base import BackendResponse

logger = logging.getLogger(__name__)


class OfflineBackend:
    """Offline backend that always returns deterministic responses."""

    name = "offline"
    priority = 40

    def __init__(self) -> None:
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True
        logger.info("offline backend initialized")

    async def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        if not self._initialized:
            await self.initialize()
        return BackendResponse(text=f"[offline] {prompt[:max_tokens]}", backend=self.name)

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        if not self._initialized:
            await self.initialize()
        return BackendResponse(text="[offline] ready", backend=self.name)

    async def stream(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256):
        if not self._initialized:
            await self.initialize()
        yield BackendResponse(text=f"[offline] {prompt[:max_tokens]}", backend=self.name)

    async def embeddings(self, text: str) -> list[float]:
        return [0.0, 0.0]

    async def health_check(self) -> bool:
        return self._initialized

    async def shutdown(self) -> None:
        self._initialized = False
