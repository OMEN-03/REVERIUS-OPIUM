from __future__ import annotations

from typing import Any, Dict


def format_debug_report(analysis: Any) -> Dict[str, Any]:
    return {
        "primary_intent": analysis.primary_intent.name if analysis.primary_intent else None,
        "confidence": analysis.primary_intent.confidence if analysis.primary_intent else None,
        "parameters": analysis.primary_intent.parameters if analysis.primary_intent else {},
        "matched_phrases": analysis.primary_intent.matched_keywords if analysis.primary_intent else [],
        "debug": analysis.debug,
    }
