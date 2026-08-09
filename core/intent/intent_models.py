from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class Intent:
    name: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    source_text: str = ""
    matched_keywords: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    execution_status: str = "pending"


@dataclass(slots=True)
class IntentDefinition:
    name: str
    keywords: List[str] = field(default_factory=list)
    handler: Optional[Any] = None
    risk_level: str = "safe"
    requires_confirmation: bool = False
    description: str = ""


@dataclass(slots=True)
class IntentAnalysis:
    primary_intent: Optional[Intent] = None
    intents: List[Intent] = field(default_factory=list)
    debug: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CommandResult:
    success: bool
    intent: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
