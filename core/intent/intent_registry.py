from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .intent_models import IntentDefinition


class IntentRegistry:
    """Registry for intents and their keyword definitions."""

    def __init__(self) -> None:
        self._definitions: Dict[str, IntentDefinition] = {}

    def register_intent(
        self,
        *,
        name: str,
        keywords: Optional[List[str]] = None,
        handler: Optional[Callable[..., Any]] = None,
        risk_level: str = "safe",
        requires_confirmation: bool = False,
        description: str = "",
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def _register(target_handler: Optional[Callable[..., Any]] = None) -> None:
            self._definitions[name.lower()] = IntentDefinition(
                name=name.lower(),
                keywords=[keyword.lower() for keyword in (keywords or [])],
                handler=target_handler,
                risk_level=risk_level,
                requires_confirmation=requires_confirmation,
                description=description or (target_handler.__doc__ if target_handler else ""),
            )

        if handler is not None:
            _register(handler)
            return handler  # type: ignore[return-value]

        _register(None)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            _register(func)
            return func

        return decorator

    def get(self, name: str) -> Optional[IntentDefinition]:
        return self._definitions.get(name.lower())

    def all(self) -> List[IntentDefinition]:
        return list(self._definitions.values())

    def find_by_keyword(self, keyword: str) -> Optional[IntentDefinition]:
        normalized = keyword.lower().strip()
        if not normalized:
            return None
        for definition in self._definitions.values():
            if any(token == normalized or normalized in token or token in normalized for token in definition.keywords):
                return definition
        return None
