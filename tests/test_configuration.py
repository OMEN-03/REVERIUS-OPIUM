import os
from pathlib import Path

from config.settings import load_settings, Settings


def test_load_settings_uses_env_variables(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    settings = load_settings()
    assert settings.log_level == "DEBUG"


def test_load_settings_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    settings = load_settings()
    assert settings.log_level == "INFO"
