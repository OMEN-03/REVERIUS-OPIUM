from __future__ import annotations

from typing import Any


class ReveriusTheme:
    BACKGROUND = "#04070d"
    PANEL = "#07111d"
    SURFACE = "#0c1724"
    BORDER = "#4f3f23"
    ACCENT = "#d2a447"
    ACCENT_SOFT = "#8c6328"
    ACCENT_DEEP = "#3b2712"
    TEXT = "#f3e7c8"
    MUTED = "#6f7b8d"
    SECONDARY = "#8d95a3"
    SUCCESS = "#48d38d"
    WARNING = "#f0b24b"
    ERROR = "#ff6b6b"
    BACKDROP = "#05070d"
    ELEVATED = "#101722"
    SURFACE_ALT = "#162132"
    STATUS_COLORS = {
        "IDLE": MUTED,
        "LISTENING": ACCENT,
        "THINKING": WARNING,
        "PROCESSING": SUCCESS,
        "EXECUTING": ACCENT,
        "RESPONDING": SUCCESS,
        "ERROR": ERROR,
        "OFFLINE": MUTED,
        "INITIALIZING": ACCENT,
        "DEGRADED": WARNING,
    }


THEME = ReveriusTheme()


def state_to_status(state: str | None) -> str:
    normalized = (state or "IDLE").strip().upper()
    return normalized if normalized in THEME.STATUS_COLORS else "IDLE"


def build_dashboard_summary(module: Any) -> dict[str, str]:
    snapshot = build_operational_snapshot(module)
    return {
        "personality": snapshot["personality"],
        "state": snapshot["state"],
        "mission": f"Mission: {snapshot['task']}",
        "operator_context": (
            f"Context: {snapshot['memory_entries']} memory entries • {snapshot['plugin_count']} plugins • "
            f"backend {snapshot['backend']}"
        ),
    }


def build_operational_snapshot(module: Any) -> dict[str, Any]:
    personality = getattr(module, "current_personality", "OMEN SHADOW CORE")
    state = state_to_status(getattr(module, "hud_ai_state", "IDLE"))
    task = getattr(module, "hud_current_task", "Awaiting command") or "Awaiting command"
    memory_entries = getattr(module, "memory_entries", {}) or {}
    plugin_count = len(getattr(module, "loaded_plugins", []) or [])

    backend = "Offline"
    try:
        import modules.ai_backend as ai_module
        if getattr(ai_module, "get_backend_info", None):
            info = ai_module.get_backend_info()
            backend = info.get("name", backend)
    except Exception:
        backend = "OpenJarvis" if getattr(module, "jarvis_available", False) else backend

    context_tags = ["Core", "AI", "Systems"]
    if task and task.lower() != "awaiting command":
        context_tags.append(task.split()[0].capitalize())
    if plugin_count:
        context_tags.append("Plugins")
    if len(memory_entries) > 0:
        context_tags.append("Memory")

    pipeline = [
        {"label": "INPUT", "state": "ACTIVE" if state in {"LISTENING", "THINKING", "PROCESSING"} else "WAITING"},
        {"label": "INTENT", "state": "ACTIVE" if state in {"THINKING", "PROCESSING", "EXECUTING"} else "WAITING"},
        {"label": "PLAN", "state": "COMPLETE" if state in {"PROCESSING", "EXECUTING", "RESPONDING"} else "WAITING"},
        {"label": "MEMORY", "state": "ACTIVE" if memory_entries else "WAITING"},
        {"label": "TOOLS", "state": "ACTIVE" if plugin_count else "WAITING"},
        {"label": "RESPONSE", "state": "COMPLETE" if state in {"RESPONDING"} else "WAITING"},
    ]

    return {
        "personality": personality,
        "state": state,
        "task": task,
        "memory_entries": len(memory_entries),
        "plugin_count": plugin_count,
        "backend": backend,
        "context_tags": context_tags,
        "pipeline": pipeline,
    }


# Backward-compatible exports expected by the tests and runtime helpers.
ACCENT = THEME.ACCENT
MUTED = THEME.MUTED
STATUS_COLORS = THEME.STATUS_COLORS
