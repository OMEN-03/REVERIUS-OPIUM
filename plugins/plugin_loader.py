from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PLUGIN_PACKAGE = "plugins"
_plugin_modules: List[Tuple[str, Any]] | None = None


def _get_package_path() -> Optional[Path]:
    try:
        package = importlib.import_module(PLUGIN_PACKAGE)
        return Path(package.__file__).resolve().parent
    except ImportError:
        return None


def _discover_modules() -> List[Tuple[str, Any]]:
    global _plugin_modules
    if _plugin_modules is not None:
        return _plugin_modules

    _plugin_modules = []
    package_path = _get_package_path()
    if package_path is None:
        return _plugin_modules

    for _, name, is_pkg in pkgutil.iter_modules([str(package_path)]):
        if name.startswith("_") or name in {"plugin_loader", "manager"}:
            continue

        module_name = f"{PLUGIN_PACKAGE}.{name}"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "handle_command") or hasattr(module, "init_plugin"):
                _plugin_modules.append((name, module))
        except Exception:
            continue

    if not any(name == "assistant" for name, _ in _plugin_modules):
        try:
            assistant_module = importlib.import_module("modules.ai_backend")
            if hasattr(assistant_module, "handle_command") or hasattr(assistant_module, "init_plugin"):
                _plugin_modules.append(("assistant", assistant_module))
        except Exception:
            pass

    return _plugin_modules


def discover_plugins() -> List[Tuple[str, Any]]:
    """Discover plugin modules under the plugins package."""
    return list(_discover_modules())


def initialize_plugins() -> List[str]:
    """Initialize plugins by calling init_plugin() if available."""
    initialized: List[str] = []
    for name, module in _discover_modules():
        try:
            init_fn = getattr(module, "init_plugin", None)
            if callable(init_fn):
                init_fn()
            initialized.append(name)
        except Exception:
            continue
    return initialized


def dispatch_command(command: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """Dispatch a command to the first plugin that can handle it."""
    normalized_command = (command or "").strip().lower()
    if not normalized_command:
        return False

    for _, module in _discover_modules():
        try:
            handler = getattr(module, "handle_command", None)
            if handler is None:
                continue

            if callable(handler):
                result = handler(normalized_command, context or {})
                if result:
                    return True
            elif isinstance(handler, dict):
                plugin_handler = handler.get(normalized_command)
                if callable(plugin_handler) and plugin_handler(normalized_command, context or {}):
                    return True
        except Exception:
            continue

    return False
