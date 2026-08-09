from __future__ import annotations

import re
from typing import Dict, List, Optional


class EntityExtractor:
    """Extract simple entities such as targets, queries, names, URLs, and dates."""

    def extract(self, text: str) -> Dict[str, str]:
        normalized = (text or "").strip()
        if not normalized:
            return {}

        entities: Dict[str, str] = {}
        url_match = re.search(r"https?://\S+", normalized, re.IGNORECASE)
        if url_match:
            entities["url"] = url_match.group(0)

        if "folder" in normalized.lower() and "called" in normalized.lower():
            parts = re.split(r"called", normalized, flags=re.IGNORECASE, maxsplit=1)
            if len(parts) > 1:
                entities["name"] = parts[1].strip().strip(" .")
                entities["type"] = "folder"

        if normalized.lower().startswith(("rename ", "change ")):
            parts = re.split(r"\s+to\s+", normalized, flags=re.IGNORECASE, maxsplit=1)
            if len(parts) == 2:
                entities["source"] = parts[0].split()[-1]
                entities["destination"] = parts[1].strip()

        if re.search(r"\b(open|launch|start|run)\b", normalized, re.IGNORECASE):
            target = normalized.strip()
            for prefix in ("open ", "launch ", "start ", "run "):
                if target.lower().startswith(prefix):
                    target = target[len(prefix):].strip()
                    break
            if target:
                entities["target"] = target

        if re.search(r"\b(search|find|look up|look for|seek)\b", normalized, re.IGNORECASE):
            # Try to extract the query following the search phrase anywhere in the text
            m = re.search(r"\b(search for|find|look for|look up|find me)\b\s*(.+)", normalized, re.IGNORECASE)
            if m:
                entities["query"] = m.group(2).strip().strip(" .?")
            else:
                for prefix in ("search for ", "find ", "look for ", "look up ", "search "):
                    if normalized.lower().startswith(prefix):
                        entities["query"] = normalized[len(prefix):].strip()
                        break
                if "query" not in entities:
                    entities["query"] = normalized.strip()

        if re.search(r"\b(delete|remove|erase)\b", normalized, re.IGNORECASE):
            entity = normalized.strip()
            for prefix in ("delete ", "remove ", "erase "):
                if entity.lower().startswith(prefix):
                    entity = entity[len(prefix):].strip()
                    break
            if entity:
                entities["target"] = entity

        return entities
