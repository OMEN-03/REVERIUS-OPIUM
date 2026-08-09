from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class PluginSpec:
    """Metadata describing a plugin's lifecycle and resource requirements."""

    name: str
    version: str = "1.0"
    description: str = ""
    dependencies: Tuple[str, ...] = ()
    required_packages: Tuple[str, ...] = ()
    estimated_ram_mb: int = 16
    estimated_cpu_percent: int = 5
    startup_time_ms: int = 50
    health_status: str = "healthy"
    supported_intents: Tuple[str, ...] = ()
    module_name: Optional[str] = None
    enabled: bool = True


class Kernel:
    """Lightweight AI kernel that routes requests to the smallest necessary plugin set."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginSpec] = {}
        self._loaded: Set[str] = set()
        self._active: Set[str] = set()
        self._intent_cache: Dict[str, Tuple[str, ...]] = {}

    def register_plugin(self, spec: PluginSpec) -> None:
        """Register a plugin spec with the kernel."""
        self._plugins[spec.name.lower()] = spec

    def discover_plugins(self, specs: List[PluginSpec]) -> None:
        """Bulk-register plugin specs."""
        for spec in specs:
            self.register_plugin(spec)

    def detect_intent(self, request: str) -> Tuple[str, float, Tuple[str, ...]]:
        """Classify a request into a broad intent and required plugin names."""
        normalized = (request or "").strip().lower()
        if not normalized:
            return "general", 0.0, ()

        if any(term in normalized for term in ("search", "find", "browse", "web", "google")):
            return "search", 0.99, ("search", "browser", "http")
        if any(term in normalized for term in ("code", "compile", "cpp", "python", "c++", "program")):
            return "coding", 0.97, ("planner", "reasoning", "code_generator", "compiler")
        if any(term in normalized for term in ("image", "vision", "ocr", "photo", "edit")):
            return "vision", 0.95, ("vision", "ocr", "image_processor")
        if any(term in normalized for term in ("voice", "speech", "audio", "music")):
            return "voice", 0.93, ("voice", "speech_recognition")
        if any(term in normalized for term in ("test", "benchmark", "diagnose", "doctor")):
            return "diagnostics", 0.94, ("benchmark", "testing", "diagnostics")
        return "general", 0.6, ("reasoning",)

    def resolve_plugins(self, request: str) -> List[PluginSpec]:
        """Resolve the minimal plugin set needed for a request."""
        intent, confidence, required_plugins = self.detect_intent(request)
        self._intent_cache[request.lower()] = (intent, *required_plugins)

        resolved: List[PluginSpec] = []
        for plugin_name in required_plugins:
            spec = self._plugins.get(plugin_name.lower())
            if spec and spec.enabled and spec.name.lower() not in self._loaded:
                resolved.append(spec)
        return resolved

    def load_plugins(self, request: str) -> List[PluginSpec]:
        """Load the plugins required for a request and mark them active."""
        plugins = self.resolve_plugins(request)
        for spec in plugins:
            self._loaded.add(spec.name.lower())
            self._active.add(spec.name.lower())
        return plugins

    def unload_idle_plugins(self, inactive_names: Optional[List[str]] = None) -> None:
        """Unload plugins that are idle and not pinned by the kernel."""
        for name in inactive_names or list(self._active):
            self._active.discard(name.lower())

    def get_status(self) -> Dict[str, Any]:
        """Return minimal kernel status for diagnostics and dashboards."""
        return {
            "loaded_plugins": sorted(self._loaded),
            "active_plugins": sorted(self._active),
            "registered_plugins": sorted(self._plugins.keys()),
        }
