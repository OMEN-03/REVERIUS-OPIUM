from __future__ import annotations

import asyncio
import logging
from typing import Any

from .base import BackendResponse, BaseBackend
from .registry import BackendRegistry
from config.settings import load_settings

logger = logging.getLogger(__name__)


class BackendManager:
    """Manages backend selection, failover, and health monitoring."""

    def __init__(self, registry: BackendRegistry | None = None, preferred_backend: str | None = None) -> None:
        self.registry = registry or BackendRegistry()
        self.settings = load_settings(path="config.toml")
        self.preferred_backend = preferred_backend or self.settings.preferred_backend
        self.current_backend: BaseBackend | None = None
        self._initialized = False
        self._set_initial_backend_hint()

    def _set_initial_backend_hint(self) -> None:
        """Choose a sensible backend immediately so callers can inspect the manager state before async init completes."""
        preferred = self.registry.get(self.preferred_backend)
        backends = self.registry.list()
        if preferred and preferred.name.lower() == "offline":
            non_offline = [backend for backend in backends if backend.name.lower() != "offline"]
            candidates = non_offline + [preferred] if non_offline else [preferred]
        else:
            candidates = [preferred] if preferred else []
            candidates.extend(backend for backend in backends if backend is not preferred)
        self.current_backend = candidates[0] if candidates else None

    async def initialize(self) -> None:
        """Initialize the preferred backend, falling back safely if needed."""
        if self._initialized and self.current_backend is not None:
            return

        self._initialized = False

        preferred = self.registry.get(self.preferred_backend)
        backends = self.registry.list()
        if preferred and preferred.name.lower() == "offline":
            non_offline = [backend for backend in backends if backend.name.lower() != "offline"]
            candidates = non_offline + [preferred] if non_offline else [preferred]
        else:
            candidates = [preferred] if preferred else []
            candidates.extend(backend for backend in backends if backend is not preferred)

        for backend in candidates:
            try:
                await backend.initialize()
                if await backend.health_check():
                    self.current_backend = backend
                    self._initialized = True
                    logger.info("backend selected", extra={"backend": backend.name})
                    return
                await backend.shutdown()
            except Exception as exc:  # pragma: no cover - defensive path
                logger.warning("backend initialization failed", extra={"backend": getattr(backend, "name", "unknown"), "error": str(exc)})

        if self.current_backend is None:
            offline_backend = self.registry.get("offline")
            if offline_backend is not None:
                try:
                    await offline_backend.initialize()
                    if await offline_backend.health_check():
                        self.current_backend = offline_backend
                except Exception as exc:  # pragma: no cover - defensive path
                    logger.warning("offline backend initialization failed", extra={"backend": offline_backend.name, "error": str(exc)})

        self._initialized = True

    async def generate(self, prompt: str, *, temperature: float | None = None, max_tokens: int | None = None) -> BackendResponse:
        """Generate a response using the current backend."""
        if not self._initialized:
            await self.initialize()
        backend = self._ensure_backend()
        return await backend.generate(prompt, temperature=temperature or self.settings.temperature, max_tokens=max_tokens or self.settings.max_tokens)

    async def chat(self, messages: list[dict[str, str]], *, temperature: float | None = None, max_tokens: int | None = None) -> BackendResponse:
        """Generate a chat response using the current backend."""
        if not self._initialized:
            await self.initialize()
        backend = self._ensure_backend()
        return await backend.chat(messages, temperature=temperature or self.settings.temperature, max_tokens=max_tokens or self.settings.max_tokens)

    async def stream(self, prompt: str, *, temperature: float | None = None, max_tokens: int | None = None):
        """Stream a response using the current backend."""
        if not self._initialized:
            await self.initialize()
        backend = self._ensure_backend()
        async for chunk in backend.stream(prompt, temperature=temperature or self.settings.temperature, max_tokens=max_tokens or self.settings.max_tokens):
            yield chunk

    def _ensure_backend(self) -> BaseBackend:
        if self.current_backend is None:
            raise RuntimeError("No backend available")
        return self.current_backend
