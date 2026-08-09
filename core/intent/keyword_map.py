from __future__ import annotations

from typing import Dict, List, Tuple


class KeywordMap:
    """Maps intents to synonyms and helper phrases."""

    def __init__(self) -> None:
        self._map: Dict[str, Tuple[str, ...]] = {
            "search": (
                "search",
                "find",
                "look for",
                "look up",
                "locate",
                "seek",
                "find me",
                "search for",
                "search the web",
            ),
            "open": (
                "open",
                "launch",
                "start",
                "run",
                "show me",
                "bring up",
            ),
            "close": (
                "close",
                "exit",
                "quit",
                "terminate",
                "shut down",
            ),
            "create": (
                "create",
                "make",
                "build",
                "generate",
                "write",
            ),
            "delete": (
                "delete",
                "remove",
                "erase",
                "clear",
                "discard",
            ),
            "edit": (
                "edit",
                "modify",
                "change",
                "update",
                "rename",
            ),
            "read": (
                "read",
                "show",
                "display",
                "view",
                "inspect",
            ),
            "save": (
                "save",
                "store",
                "remember",
                "keep",
            ),
            "download": (
                "download",
                "get",
                "fetch",
            ),
            "upload": (
                "upload",
                "send",
                "attach",
            ),
            "play": (
                "play",
                "start playing",
                "resume",
            ),
            "pause": (
                "pause",
                "stop playing",
            ),
            "stop": (
                "stop",
                "halt",
                "cancel",
                "terminate",
            ),
            "navigate": (
                "go to",
                "navigate to",
                "open page",
                "visit",
            ),
            "execute": (
                "execute",
                "run",
                "perform",
                "do",
            ),
            "help": (
                "help",
                "what can you do",
                "commands",
                "capabilities",
            ),
        }

    def get_keywords(self, intent_name: str) -> Tuple[str, ...]:
        return self._map.get(intent_name.lower(), ())

    def all(self) -> Dict[str, Tuple[str, ...]]:
        return dict(self._map)

    def match(self, text: str) -> List[Tuple[str, str]]:
        normalized = (text or "").strip().lower()
        if not normalized:
            return []
        matches: List[Tuple[str, str]] = []
        for intent_name, keywords in self._map.items():
            for keyword in keywords:
                if keyword.lower() in normalized:
                    matches.append((intent_name, keyword))
                    break
        return matches
