from .architecture import (
    CommandRouter,
    EthicalDecision,
    EthicalFoundation,
    EventBus,
    PluginRegistry,
    evaluate_user_request,
    get_ethical_foundation_prompt,
)
from .kernel import Kernel, PluginSpec
import importlib
from .orchestrator import AIOrchestrator, PipelineResult

__all__ = [
    "CommandRouter",
    "EthicalDecision",
    "EthicalFoundation",
    "EventBus",
    "PluginRegistry",
    "Kernel",
    "PluginSpec",
    "AIOrchestrator",
    "PipelineResult",
    "evaluate_user_request",
    "get_ethical_foundation_prompt",
]


def __getattr__(name: str):
    if name == "app":
        return importlib.import_module("core.app")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")