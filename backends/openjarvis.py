from __future__ import annotations

import logging
from typing import Any

from .base import BackendResponse
from .errors import AuthenticationError, InitializationError

logger = logging.getLogger(__name__)


class OpenJarvisBackend:
    """Adapter for the optional OpenJarvis SDK."""

    name = "openjarvis"
    priority = 10

    def __init__(self) -> None:
        self._initialized = False
        self._client: Any | None = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        try:
            from openjarvis import Jarvis  # type: ignore
        except ImportError as exc:
            raise InitializationError("OpenJarvis SDK is not available") from exc
        self._client = Jarvis()
        self._initialized = True
        logger.info("openjarvis backend initialized")

    async def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        if not self._initialized:
            await self.initialize()
        assert self._client is not None
        response = self._client.ask(prompt, temperature=temperature, max_tokens=max_tokens)
        return BackendResponse(text=response, backend=self.name)

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        if not self._initialized:
            await self.initialize()
        return BackendResponse(text="openjarvis chat", backend=self.name)

    async def stream(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256):
        if not self._initialized:
            await self.initialize()
        yield BackendResponse(text=f"openjarvis:{prompt}", backend=self.name)

    async def embeddings(self, text: str) -> list[float]:
        return [float(len(text))]

    async def health_check(self) -> bool:
        return self._initialized and self._client is not None

    async def shutdown(self) -> None:
        self._initialized = False
        self._client = None
