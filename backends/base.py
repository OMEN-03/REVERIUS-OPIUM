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

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.0, max_tokens: int = 256) -> BackendResponse:
        """Generate a chat response from a list of messages."""

    async def stream(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256) -> AsyncIterator[BackendResponse]:
        """Stream a response incrementally."""

    async def embeddings(self, text: str) -> list[float]:
        """Generate embeddings for text."""

    async def health_check(self) -> bool:
        """Return whether the backend is healthy."""

    async def shutdown(self) -> None:
        """Release backend resources."""
