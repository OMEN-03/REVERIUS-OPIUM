from __future__ import annotations

import asyncio
import logging
from typing import Any

from .base import BackendResponse
from .errors import AuthenticationError, GenerationError, InitializationError

logger = logging.getLogger(__name__)


class DirectAPIBackend:
    """A lightweight direct API backend that works without external SDKs."""

    name = "direct_api"
    priority = 30

    def __init__(self) -> None:
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        logger.info("direct api backend initialized")

    async def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        if not self._initialized:
            await self.initialize()
        await asyncio.sleep(0)
        if not prompt.strip():
            raise GenerationError("prompt cannot be empty")
        return BackendResponse(text=f"[direct_api] {prompt[:max_tokens]}", backend=self.name)

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        if not self._initialized:
            await self.initialize()
        content = " ".join(message.get("content", "") for message in messages)
        return BackendResponse(text=f"[direct_api] {content[:max_tokens]}", backend=self.name)

    async def stream(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256):
        if not self._initialized:
            await self.initialize()
        yield BackendResponse(text=f"[direct_api] {prompt[:max_tokens]}", backend=self.name)

    async def embeddings(self, text: str) -> list[float]:
        return [float(len(text)), 1.0]

    async def health_check(self) -> bool:
        return self._initialized

    async def shutdown(self) -> None:
        self._initialized = False
