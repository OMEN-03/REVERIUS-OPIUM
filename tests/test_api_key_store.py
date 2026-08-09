from pathlib import Path

from utils.api_key_store import clear_api_key, load_saved_api_key, save_api_key


def test_save_and_load_api_key(tmp_path, monkeypatch):
    monkeypatch.setattr("utils.api_key_store.DEFAULT_API_KEY_FILE", tmp_path / "api_key.txt")

    clear_api_key()
    assert load_saved_api_key() is None

    save_api_key("sk-test-123")
    assert load_saved_api_key() == "sk-test-123"

    clear_api_key()
    assert load_saved_api_key() is None
