from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional, Protocol


@dataclass(slots=True)
class BackendResponse:
    """Structured response produced by a backend."""

    text: str
    backend: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseBackend(Protocol):
    """Protocol for AI backend implementations."""

    name: str
    priority: int

    async def initialize(self) -> None:
        """Initialize backend resources."""

    async def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        """Generate a response from a prompt."""
        raise NotImplementedError("Subclass must implement generate()")

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        """Generate a chat response from a list of messages."""
        raise NotImplementedError("Subclass must implement chat()")

    async def stream(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256) -> AsyncIterator[BackendResponse]:
        """Stream a response incrementally."""
        raise NotImplementedError("Subclass must implement stream()")
        yield  # Make this an async generator

    async def embeddings(self, text: str) -> list[float]:
        """Generate embeddings for text."""
        raise NotImplementedError("Subclass must implement embeddings()")

    async def health_check(self) -> bool:
        """Return whether the backend is healthy."""
        raise NotImplementedError("Subclass must implement health_check()")

    async def shutdown(self) -> None:
        """Release backend resources."""
