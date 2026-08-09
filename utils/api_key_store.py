import os
from pathlib import Path

DEFAULT_API_KEY_FILE = Path.home() / ".reverius_openai_api_key"


def _get_api_key_file() -> Path:
    return Path(os.environ.get("REVERIUS_API_KEY_FILE", str(DEFAULT_API_KEY_FILE)))


def save_api_key(api_key: str) -> bool:
    try:
        key = (api_key or "").strip()
        if not key:
            return False
        _get_api_key_file().write_text(key, encoding="utf-8")
        os.environ["OPENAI_API_KEY"] = key
        os.environ["REVERIUS_OPENAI_API_KEY"] = key
        os.environ["OMEN_OPENAI_API_KEY"] = key
        return True
    except Exception:
        return False


def load_saved_api_key() -> str | None:
    try:
        file_path = _get_api_key_file()
        if not file_path.exists():
            return None
        value = file_path.read_text(encoding="utf-8").strip()
        return value or None
    except Exception:
        return None


def clear_api_key() -> bool:
    try:
        file_path = _get_api_key_file()
        if file_path.exists():
            file_path.unlink()
        for env_name in ("OPENAI_API_KEY", "REVERIUS_OPENAI_API_KEY", "OMEN_OPENAI_API_KEY"):
            os.environ.pop(env_name, None)
        return True
    except Exception:
        return False
