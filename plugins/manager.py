from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PluginMetadata:
    """Metadata that describes a plugin."""

    name: str
    version: str = "0.1.0"
    description: str = ""
    permissions: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)


class BasePlugin(Protocol):
    """Protocol for runtime plugins."""

    metadata: PluginMetadata

    def initialize(self) -> None:
        """Initialize plugin state."""

    def shutdown(self) -> None:
        """Release plugin resources."""


class PluginManager:
    """Simple hot-loadable plugin manager with metadata support."""

    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}
        self._metadata: dict[str, PluginMetadata] = {}

    def register(self, plugin: BasePlugin, metadata: PluginMetadata | None = None) -> None:
        """Register a plugin instance."""
        resolved_name = metadata.name if metadata else getattr(plugin, "name", plugin.__class__.__name__)
        self._plugins[resolved_name] = plugin
        self._metadata[resolved_name] = metadata or PluginMetadata(name=resolved_name)

    def load_from_module(self, module_name: str) -> BasePlugin | None:
        """Load a plugin from an importable module name."""
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            logger.warning("plugin import failed", extra={"module": module_name, "error": str(exc)})
            return None

        plugin = getattr(module, "PLUGIN_INSTANCE", None)
        if plugin is None:
            plugin = getattr(module, "plugin", None)
        if plugin is None:
            return None

        metadata = getattr(module, "PLUGIN_METADATA", None)
        self.register(plugin, metadata)
        return plugin

    def unload(self, name: str) -> None:
        """Unload a plugin by name."""
        plugin = self._plugins.pop(name, None)
        if plugin is not None and hasattr(plugin, "shutdown"):
            plugin.shutdown()
        self._metadata.pop(name, None)

    def list_plugins(self) -> list[tuple[str, PluginMetadata]]:
        """Return registered plugins and metadata."""
        return [(name, self._metadata[name]) for name in self._plugins]
