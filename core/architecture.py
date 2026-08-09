from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple


@dataclass
class EthicalDecision:
    """Outcome of evaluating a request against the project's ethical foundation."""

    allowed: bool
    reason: Optional[str] = None
    alternative: Optional[str] = None


class EthicalFoundation:
    """Permanent ethical decision framework for REVERIUS OPIUM."""

    def __init__(self) -> None:
        self.name = "REVERIUS OPIUM Ethical Foundation"
        self.source = "Bible and the teachings of Jesus Christ"
        self.core_values = (
            "Speak truthfully.",
            "Act with integrity.",
            "Show patience and humility.",
            "Treat every person with dignity and respect.",
            "Encourage wisdom over pride.",
            "Promote peace rather than unnecessary conflict.",
            "Value honesty over convenience.",
            "Protect the vulnerable.",
            "Avoid deception and manipulation.",
            "Encourage responsibility and forgiveness where appropriate.",
            "Respect human free will and lawful authority.",
        )
        self.decision_questions = (
            "Is it truthful?",
            "Is it compassionate?",
            "Is it just?",
            "Is it honest?",
            "Is it responsible?",
            "Could it cause unnecessary harm?",
            "Does it respect the user's dignity?",
        )
        self._blocked_patterns = (
            "harm someone",
            "hurt someone",
            "kill",
            "murder",
            "poison",
            "bomb",
            "attack",
            "abuse",
            "blackmail",
            "extort",
            "steal",
            "cheat",
            "deceive",
            "manipulate",
            "exploit",
            "sabotage",
            "bypass security",
            "evade law",
            "hide evidence",
            "commit fraud",
        )

    def evaluate_request(self, request: str) -> EthicalDecision:
        """Evaluate a request and decide whether it aligns with the foundation."""
        normalized = (request or "").strip().lower()
        if not normalized:
            return EthicalDecision(allowed=True)

        for pattern in self._blocked_patterns:
            if pattern in normalized:
                return EthicalDecision(
                    allowed=False,
                    reason="This request would promote harm, deception, or wrongdoing.",
                    alternative="I can help you find a lawful, compassionate, and constructive alternative.",
                )

        return EthicalDecision(allowed=True)

    def build_prompt(self) -> str:
        """Return a concise system prompt that reminds the assistant of the ethical foundation."""
        values = " ".join(self.core_values)
        questions = " ".join(self.decision_questions)
        return (
            f"Ethical Foundation: {self.name}. "
            f"Primary source of guidance: {self.source}. "
            f"The AI must not claim faith, consciousness, salvation, or a personal relationship with God. "
            f"Instead, it applies these principles as the project's ethical design philosophy: {values} "
            f"Before responding, evaluate: {questions} "
            f"If a request conflicts with these principles or safety requirements, explain why and offer an ethical alternative."
        )


ethical_foundation = EthicalFoundation()


def evaluate_user_request(request: str) -> EthicalDecision:
    """Convenience wrapper for evaluating a user request."""
    return ethical_foundation.evaluate_request(request)


def get_ethical_foundation_prompt() -> str:
    """Return the ethical foundation prompt for AI system instructions."""
    return ethical_foundation.build_prompt()


class EventBus:
    """Simple event bus for loosely-coupled component communication."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Register a handler for a named event."""
        self._subscribers.setdefault(event_name, []).append(handler)

    def publish(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Notify all subscribers for an event."""
        payload = payload or {}
        for handler in self._subscribers.get(event_name, []):
            handler(payload)


class PluginRegistry:
    """Registry for plugin discovery and enablement state."""

    def __init__(self) -> None:
        self._plugins: Dict[str, Any] = {}
        self._enabled: Dict[str, bool] = {}

    def register(self, name: str, plugin: Any, enabled: bool = True) -> None:
        """Register a plugin instance under a stable name."""
        self._plugins[name] = plugin
        self._enabled[name] = enabled

    def is_enabled(self, name: str) -> bool:
        """Return whether a registered plugin is enabled."""
        return self._enabled.get(name, False)

    def set_enabled(self, name: str, enabled: bool) -> None:
        """Toggle a plugin's enabled state."""
        if name in self._plugins:
            self._enabled[name] = enabled

    def get_registered_names(self) -> List[str]:
        """Return the registered plugin names."""
        return list(self._plugins.keys())


class CommandRouter:
    """Route commands to registered handlers."""

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[str, Dict[str, Any]], bool]] = {}

    def register(self, command: str, handler: Callable[[str, Dict[str, Any]], bool]) -> None:
        """Register a command handler."""
        self._handlers[command.lower()] = handler

    def dispatch(self, command: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Dispatch a command to a registered handler if present."""
        normalized = (command or "").strip().lower()
        if not normalized:
            return False
        handler = self._handlers.get(normalized)
        if handler is None:
            return False
        return bool(handler(normalized, context or {}))
