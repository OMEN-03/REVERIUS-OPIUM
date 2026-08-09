from __future__ import annotations

from typing import Any

from .base import BaseBackend


class BackendRegistry:
    """Registry that manages available backend implementations."""

    def __init__(self) -> None:
        self._backends: dict[str, BaseBackend] = {}

    def register(self, backend: BaseBackend) -> None:
        """Register a backend instance."""
        self._backends[backend.name] = backend

    def get(self, name: str) -> BaseBackend | None:
        """Return a backend by name."""
        return self._backends.get(name)

    def list(self) -> list[BaseBackend]:
        """Return all registered backends sorted by priority."""
        return sorted(self._backends.values(), key=lambda backend: backend.priority)

    def names(self) -> list[str]:
        """Return registered backend names."""
        return list(self._backends.keys())
