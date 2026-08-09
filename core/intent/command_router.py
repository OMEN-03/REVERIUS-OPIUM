from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .intent_models import CommandResult, Intent
from .intent_registry import IntentRegistry


class CommandRouter:
    """Resolve intents to executable handlers and validate the resulting action."""

    def __init__(self, registry: Optional[IntentRegistry] = None) -> None:
        self.registry = registry or IntentRegistry()
        self._handlers: Dict[str, Any] = {}

    def register_handler(self, intent_name: str, handler: Any) -> None:
        self._handlers[intent_name.lower()] = handler

    def route(self, intent: Intent) -> CommandResult:
        definition = self.registry.get(intent.name)
        if definition is None:
            return CommandResult(
                success=False,
                intent=intent.name,
                message="No handler is registered for this intent.",
                error="intent_not_found",
            )

        if intent.requires_confirmation and definition.requires_confirmation:
            return CommandResult(
                success=False,
                intent=intent.name,
                message="Confirmation required before executing this action.",
                error="confirmation_required",
            )

        handler = definition.handler or self._handlers.get(intent.name.lower())
        if handler is None:
            return CommandResult(
                success=False,
                intent=intent.name,
                message="No executable handler was found.",
                error="handler_not_found",
            )

        try:
            result = handler(intent.parameters)
            if isinstance(result, CommandResult):
                return result
            if isinstance(result, dict):
                return CommandResult(success=True, intent=intent.name, message="Execution completed.", data=result)
            return CommandResult(success=True, intent=intent.name, message="Execution completed.", data={"output": result})
        except Exception as exc:  # pragma: no cover - defensive
            return CommandResult(success=False, intent=intent.name, message="Execution failed.", error=str(exc))
