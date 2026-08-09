from __future__ import annotations

import difflib
import re
from typing import Any, Dict, List, Optional

from .command_router import CommandRouter
from .entity_extractor import EntityExtractor
from .intent_models import CommandResult, Intent, IntentAnalysis
from .intent_registry import IntentRegistry
from .keyword_map import KeywordMap


class IntentEngine:
    """Recognize commands and intents using a registry-based parser with lightweight heuristics."""

    def __init__(self, registry: Optional[IntentRegistry] = None, router: Optional[CommandRouter] = None) -> None:
        self.registry = registry or IntentRegistry()
        self.router = router or CommandRouter(self.registry)
        self.keyword_map = KeywordMap()
        self.entity_extractor = EntityExtractor()
        self._aliases: Dict[str, str] = {}

        self._register_builtin_intents()

    def _register_builtin_intents(self) -> None:
        self.registry.register_intent(name="search", keywords=["search", "find", "look for", "look up", "locate", "seek"], risk_level="safe")
        self.registry.register_intent(name="open", keywords=["open", "launch", "start", "run", "bring up"], risk_level="low")
        self.registry.register_intent(name="close", keywords=["close", "exit", "quit", "terminate", "shut down"], risk_level="higher")
        self.registry.register_intent(name="create", keywords=["create", "make", "build", "generate", "write"], risk_level="low")
        self.registry.register_intent(name="delete", keywords=["delete", "remove", "erase", "clear", "discard"], risk_level="higher", requires_confirmation=True)
        self.registry.register_intent(name="edit", keywords=["edit", "modify", "change", "update", "rename"], risk_level="higher")
        self.registry.register_intent(name="read", keywords=["read", "show", "display", "view", "inspect"], risk_level="safe")
        self.registry.register_intent(name="save", keywords=["save", "store", "remember", "keep"], risk_level="safe")
        self.registry.register_intent(name="download", keywords=["download", "get", "fetch"], risk_level="safe")
        self.registry.register_intent(name="upload", keywords=["upload", "send", "attach"], risk_level="safe")
        self.registry.register_intent(name="play", keywords=["play", "start playing", "resume"], risk_level="low")
        self.registry.register_intent(name="pause", keywords=["pause", "stop playing"], risk_level="low")
        self.registry.register_intent(name="stop", keywords=["stop", "halt", "cancel", "terminate"], risk_level="low")
        self.registry.register_intent(name="navigate", keywords=["go to", "navigate to", "open page", "visit"], risk_level="low")
        self.registry.register_intent(name="execute", keywords=["execute", "run", "perform", "do"], risk_level="higher")
        self.registry.register_intent(name="help", keywords=["help", "what can you do", "commands", "capabilities"], risk_level="safe")

        self.router.register_handler("search", self._default_search_handler)
        self.router.register_handler("open", self._default_open_handler)
        self.router.register_handler("close", self._default_close_handler)
        self.router.register_handler("create", self._default_create_handler)
        self.router.register_handler("delete", self._default_delete_handler)
        self.router.register_handler("edit", self._default_edit_handler)
        self.router.register_handler("read", self._default_read_handler)
        self.router.register_handler("help", self._default_help_handler)

    def analyze(self, text: str, context: Optional[Dict[str, Any]] = None) -> IntentAnalysis:
        normalized = (text or "").strip()
        if not normalized:
            return IntentAnalysis()

        # Handle short follow-up phrases by inheriting previous intent if present
        previous = None
        if context:
            previous = context.get("previous_intent")
        if previous and isinstance(previous, Intent):
            if len(normalized.split()) <= 6 or re.match(r"^(for|about|on|with)\b", normalized, re.IGNORECASE):
                merged = f"{previous.parameters.get('query','')} {normalized.lower()}".strip()
                candidate = self._build_intent(previous.name, previous.matched_keywords[0] if previous.matched_keywords else previous.name, merged, context=context)
                return IntentAnalysis(primary_intent=candidate, intents=[candidate], debug={"merged_from_previous": True})

        intent_candidates: List[Intent] = []
        matched_intents: List[Intent] = []
        for intent_name, keyword in self.keyword_map.match(normalized):
            candidate = self._build_intent(intent_name, keyword, normalized, context=context)
            intent_candidates.append(candidate)
            matched_intents.append(candidate)

        if not matched_intents:
            for definition in self.registry.all():
                for keyword in definition.keywords:
                    if keyword in normalized.lower():
                        candidate = self._build_intent(definition.name, keyword, normalized, context=context)
                        intent_candidates.append(candidate)
                        matched_intents.append(candidate)
                        break

        if not matched_intents:
            fuzzy_matches = self._fuzzy_match(normalized)
            if fuzzy_matches:
                for intent_name, keyword in fuzzy_matches:
                    candidate = self._build_intent(intent_name, keyword, normalized, context=context)
                    intent_candidates.append(candidate)
                    matched_intents.append(candidate)

        if not matched_intents:
            return IntentAnalysis(primary_intent=None, intents=[], debug={"message": "No intent recognized"})

        ranked = sorted(intent_candidates, key=lambda item: item.confidence, reverse=True)
        primary = ranked[0]
        if len(ranked) > 1:
            primary = self._merge_multi_intent(ranked, normalized)

        if primary.name == "open" and "target" not in primary.parameters and "it" in normalized.lower():
            primary.requires_confirmation = True
            primary.parameters["target"] = "unknown"

        if primary.name == "delete" and primary.confidence > 0.7:
            primary.requires_confirmation = True

        debug = {
            "input": normalized,
            "matched_phrases": [item.matched_keywords[0] if item.matched_keywords else "" for item in ranked],
            "confidence": primary.confidence,
        }
        return IntentAnalysis(primary_intent=primary, intents=ranked, debug=debug)

    def execute(self, intent: Intent) -> CommandResult:
        return self.router.route(intent)

    def add_alias(self, alias: str, target_intent: str) -> None:
        self._aliases[alias.lower().strip()] = target_intent.lower().strip()

    def remove_alias(self, alias: str) -> None:
        self._aliases.pop(alias.lower().strip(), None)

    def list_aliases(self) -> Dict[str, str]:
        return dict(self._aliases)

    def reset_aliases(self) -> None:
        self._aliases.clear()

    def _build_intent(self, intent_name: str, keyword: str, text: str, context: Optional[Dict[str, Any]] = None) -> Intent:
        normalized_text = (text or "").strip()
        confidence = self._confidence_for(intent_name, keyword, normalized_text)
        parameters = self._extract_parameters(intent_name, normalized_text, context=context)
        requires_confirmation = self._requires_confirmation(intent_name, parameters)
        return Intent(
            name=intent_name.lower(),
            confidence=confidence,
            parameters=parameters,
            source_text=normalized_text,
            matched_keywords=[keyword],
            required_permissions=[],
            requires_confirmation=requires_confirmation,
            execution_status="pending",
        )

    def _extract_parameters(self, intent_name: str, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        parameters: Dict[str, Any] = {}
        entities = self.entity_extractor.extract(text)
        if intent_name == "search":
            query = entities.get("query") or self._extract_query(text)
            if not query:
                query = text
            parameters["query"] = query
        elif intent_name == "open":
            target = entities.get("target") or self._target_from_text(text)
            if target:
                parameters["target"] = target
        elif intent_name == "create":
            if entities.get("name"):
                parameters["name"] = entities["name"]
            if entities.get("type"):
                parameters["type"] = entities["type"]
        elif intent_name == "edit":
            parameters.update({key: value for key, value in entities.items() if key in {"source", "destination"}})
        elif intent_name == "delete":
            parameters["target"] = entities.get("target") or text

        previous = None
        if context:
            previous = context.get("previous_intent")
        if previous and isinstance(previous, Intent):
            if intent_name == "search" and "query" in previous.parameters:
                prior_query = previous.parameters.get("query")
                if isinstance(prior_query, str) and prior_query.strip():
                    parameters["query"] = f"{prior_query} {text}".strip()
        return parameters

    def _extract_query(self, text: str) -> str:
        cleaned = text.strip()
        lowered = cleaned.lower()
        # Try to find common search prefixes anywhere in the text
        m = re.search(r"\b(search for|find|look for|look up|find me)\b\s*(.+)", cleaned, re.IGNORECASE)
        if m:
            return m.group(2).strip(" .?",)
        for prefix in ("search for ", "find ", "look for ", "look up ", "search ", "find me "):
            if lowered.startswith(prefix):
                return cleaned[len(prefix):].strip()
        return cleaned

    def _target_from_text(self, text: str) -> str:
        cleaned = text.strip()
        for prefix in ("open ", "launch ", "start ", "run ", "show me ", "bring up "):
            if cleaned.lower().startswith(prefix):
                return cleaned[len(prefix):].strip()
        return cleaned

    def _requires_confirmation(self, intent_name: str, parameters: Dict[str, Any]) -> bool:
        if intent_name in {"delete", "execute"}:
            return True
        if intent_name == "open" and ("target" not in parameters or parameters.get("target", "").lower() in {"it", "that"}):
            return True
        return False

    def _confidence_for(self, intent_name: str, keyword: str, text: str) -> float:
        base = 0.8
        if keyword in text.lower():
            base += 0.08
        if intent_name in {"search", "open", "close", "delete", "edit"}:
            base += 0.04
        if self._is_direct_command(text):
            base += 0.04
        if base > 0.99:
            return 0.99
        return round(base, 2)

    def _fuzzy_match(self, text: str) -> List[Tuple[str, str]]:
        normalized = text.lower()
        matches: List[Tuple[str, str]] = []
        for intent_name, keywords in self.keyword_map.all().items():
            for keyword in keywords:
                if keyword.lower() in normalized:
                    matches.append((intent_name, keyword))
                    break
        if matches:
            return matches

        for intent_name in self.registry.all():
            for keyword in intent_name.keywords:
                if len(keyword) >= 3:
                    close = difflib.get_close_matches(normalized, [keyword], n=1, cutoff=0.75)
                    if close:
                        return [(intent_name.name, close[0])]
        return []

    def _merge_multi_intent(self, intents: List[Intent], text: str) -> Intent:
        if len(intents) < 2:
            return intents[0]
        primary = max(intents, key=lambda item: item.confidence)
        if primary.name == "open" and any(item.name == "search" for item in intents):
            primary.parameters["query"] = text
        return primary

    def _is_direct_command(self, text: str) -> bool:
        return bool(re.match(r"^(open|close|search|find|delete|create|edit|rename|help|play|pause|stop)\b", text, re.IGNORECASE))

    def _default_search_handler(self, parameters: Dict[str, Any]) -> CommandResult:
        query = parameters.get("query") or ""
        return CommandResult(success=True, intent="search", message=f"Searching for {query}", data={"query": query})

    def _default_open_handler(self, parameters: Dict[str, Any]) -> CommandResult:
        target = parameters.get("target") or ""
        return CommandResult(success=True, intent="open", message=f"Opening {target}", data={"target": target})

    def _default_close_handler(self, parameters: Dict[str, Any]) -> CommandResult:
        target = parameters.get("target") or ""
        return CommandResult(success=True, intent="close", message=f"Closing {target}", data={"target": target})

    def _default_create_handler(self, parameters: Dict[str, Any]) -> CommandResult:
        name = parameters.get("name") or ""
        kind = parameters.get("type") or "item"
        return CommandResult(success=True, intent="create", message=f"Creating {kind} {name}", data={"name": name, "type": kind})

    def _default_delete_handler(self, parameters: Dict[str, Any]) -> CommandResult:
        target = parameters.get("target") or ""
        return CommandResult(success=True, intent="delete", message=f"Deleting {target}", data={"target": target})

    def _default_edit_handler(self, parameters: Dict[str, Any]) -> CommandResult:
        source = parameters.get("source") or ""
        destination = parameters.get("destination") or ""
        return CommandResult(success=True, intent="edit", message=f"Editing {source} to {destination}", data={"source": source, "destination": destination})

    def _default_read_handler(self, parameters: Dict[str, Any]) -> CommandResult:
        query = parameters.get("query") or ""
        return CommandResult(success=True, intent="read", message=f"Reading {query}", data={"query": query})

    def _default_help_handler(self, parameters: Dict[str, Any]) -> CommandResult:
        return CommandResult(success=True, intent="help", message="Here are the supported commands.", data={"commands": ["search", "open", "close", "create", "delete", "edit", "read", "help"]})
