# =========================================================
# REVERIUS OPIUM configuration module
# =========================================================
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import logging
import os
import sys

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    class _DotenvStub:
        @staticmethod
        def load_dotenv(*args, **kwargs) -> bool:
            return False
    dotenv = _DotenvStub()

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.11+ ships with tomllib
    tomllib = None  # type: ignore[assignment]

# =========================================================
# Runtime paths
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSET_ROOT = PROJECT_ROOT / "assets"
DATA_ROOT = PROJECT_ROOT / "data"
CONFIG_ROOT = PROJECT_ROOT / "config"
PLUGIN_ROOT = PROJECT_ROOT / "plugins"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.toml"

# =========================================================
# Logging setup
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("reverius")
logger.setLevel(logging.INFO)

# =========================================================
# Optional compatibility imports
# =========================================================
MISSING_MODULES: list[str] = []

try:
    import webbrowser
    import re
    import requests
    import urllib.parse
    import http.server
    import socketserver
    import html
    import io
    import json
    import socket
    import random
    import threading
    import subprocess
    import base64
    import hashlib
    import secrets
    import math
    import time
    import platform
    import psutil
except ImportError as e:
    logger.error("Critical module missing: %s", e)
    sys.exit(1)

try:
    import wikipedia
except ImportError:
    MISSING_MODULES.append("wikipedia")
    logger.warning("Wikipedia module not available")

try:
    import pyttsx3
except ImportError:
    MISSING_MODULES.append("pyttsx3")
    logger.warning("Text-to-speech disabled (pyttsx3 not found)")

try:
    import customtkinter as ctk
    import tkinter as tk
except ImportError:
    MISSING_MODULES.append("customtkinter")
    logger.warning("customtkinter not available")

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    MISSING_MODULES.append("matplotlib")
    logger.warning("Matplotlib not available - graphs disabled")

# =========================================================
# Settings dataclass
# =========================================================
@dataclass(frozen=True)
class Settings:
    log_level: str = "INFO"
    openai_api_key: Optional[str] = None
    reverius_openai_api_key: Optional[str] = None
    omen_openai_api_key: Optional[str] = None
    auth_token: str = "REVERIUS"
    enable_voice: bool = False
    ui_mode: str = "console"
    project_root: Path = PROJECT_ROOT
    asset_root: Path = ASSET_ROOT
    data_root: Path = DATA_ROOT
    config_root: Path = CONFIG_ROOT
    plugin_root: Path = PLUGIN_ROOT
    preferred_backend: str = "offline"
    timeout_seconds: int = 10
    temperature: float = 0.2
    max_tokens: int = 512
    streaming: bool = True
    vision_enabled: bool = False
    memory_backend: str = "sqlite"
    plugins_enabled: bool = True
    nvidia_api_key: Optional[str] = None
    nvidia_model: str = "deepseek-ai/deepseek-v4-flash"
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_reasoning_effort: str = "high"


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _resolve_value(env_name: str, config_value: Any, default: Any = None) -> Any:
    if env_name in os.environ:
        return os.environ[env_name]
    if config_value is not None:
        return config_value
    return default


def _load_toml_settings(config_path: Path) -> dict[str, Any]:
    if not config_path.exists() or tomllib is None:
        return {}

    try:
        with config_path.open("rb") as config_file:
            return tomllib.load(config_file)
    except Exception:
        return {}


def load_settings(path: str | Path | None = None) -> Settings:
    """Load runtime settings from environment variables and optional TOML config."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    raw_config = _load_toml_settings(config_path)

    ai_config = raw_config.get("ai", {}) if isinstance(raw_config, dict) else {}
    logging_config = raw_config.get("logging", {}) if isinstance(raw_config, dict) else {}
    voice_config = raw_config.get("voice", {}) if isinstance(raw_config, dict) else {}
    vision_config = raw_config.get("vision", {}) if isinstance(raw_config, dict) else {}
    memory_config = raw_config.get("memory", {}) if isinstance(raw_config, dict) else {}
    plugins_config = raw_config.get("plugins", {}) if isinstance(raw_config, dict) else {}

    settings = Settings(
        log_level=str(_resolve_value("LOG_LEVEL", logging_config.get("level", "INFO"), "INFO")).upper(),
        openai_api_key=_resolve_value("OPENAI_API_KEY", ai_config.get("api_key"), None),
        reverius_openai_api_key=_resolve_value("REVERIUS_OPENAI_API_KEY", ai_config.get("reverius_api_key"), None),
        omen_openai_api_key=_resolve_value("OMEN_OPENAI_API_KEY", ai_config.get("omen_api_key"), None),
        auth_token=str(_resolve_value("REVERIUS_AUTH_TOKEN", raw_config.get("auth_token"), os.environ.get("OMEN_AUTH_TOKEN") or "REVERIUS")),
        enable_voice=_parse_bool(_resolve_value("ENABLE_VOICE", voice_config.get("enabled", False), False)),
        ui_mode=str(_resolve_value("UI_MODE", raw_config.get("ui_mode", "console"), "console")).lower(),
        preferred_backend=str(_resolve_value("PREFERRED_BACKEND", ai_config.get("preferred_backend", "offline"), "offline")),
        timeout_seconds=int(_resolve_value("TIMEOUT_SECONDS", ai_config.get("timeout_seconds", 10), 10)),
        temperature=float(_resolve_value("TEMPERATURE", ai_config.get("temperature", 0.2), 0.2)),
        max_tokens=int(_resolve_value("MAX_TOKENS", ai_config.get("max_tokens", 512), 512)),
        streaming=_parse_bool(_resolve_value("STREAMING", ai_config.get("streaming", True), True)),
        vision_enabled=_parse_bool(_resolve_value("VISION_ENABLED", vision_config.get("enabled", False), False)),
        memory_backend=str(_resolve_value("MEMORY_BACKEND", memory_config.get("backend", "sqlite"), "sqlite")),
        plugins_enabled=_parse_bool(_resolve_value("PLUGINS_ENABLED", plugins_config.get("enabled", True), True)),
        nvidia_api_key=_resolve_value("NVIDIA_API_KEY", ai_config.get("nvidia_api_key"), None),
        nvidia_model=str(_resolve_value("NVIDIA_MODEL", ai_config.get("nvidia_model", "deepseek-ai/deepseek-v4-flash"), "deepseek-ai/deepseek-v4-flash")),
        nvidia_base_url=str(_resolve_value("NVIDIA_BASE_URL", ai_config.get("nvidia_base_url", "https://integrate.api.nvidia.com/v1"), "https://integrate.api.nvidia.com/v1")),
        nvidia_reasoning_effort=str(_resolve_value("NVIDIA_REASONING_EFFORT", ai_config.get("nvidia_reasoning_effort", "high"), "high")).lower(),
    )

    logger.setLevel(getattr(logging, settings.log_level, logging.INFO))
    return settings


SETTINGS = load_settings()
