import asyncio

from backends.nvidia import NvidiaDeepSeekBackend
from config.settings import load_settings


def test_load_settings_reads_nvidia_configuration(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    monkeypatch.setenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4-flash")
    monkeypatch.setenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    monkeypatch.setenv("NVIDIA_REASONING_EFFORT", "high")

    settings = load_settings(path="config.toml")

    assert settings.nvidia_api_key == "test-key"
    assert settings.nvidia_model == "deepseek-ai/deepseek-v4-flash"
    assert settings.nvidia_base_url == "https://integrate.api.nvidia.com/v1"
    assert settings.nvidia_reasoning_effort == "high"


def test_nvidia_backend_reports_not_configured_without_key(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    backend = NvidiaDeepSeekBackend()

    assert backend.get_status()["status"] == "NOT CONFIGURED"
    assert backend.get_status()["configured"] is False


def test_nvidia_backend_generate_uses_configured_payload(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    monkeypatch.setenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4-flash")
    monkeypatch.setenv("NVIDIA_REASONING_EFFORT", "max")

    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "hello from nvidia"}}]}

    def fake_post(url, headers=None, json=None, timeout=30):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr("backends.nvidia.requests.post", fake_post)

    backend = NvidiaDeepSeekBackend()
    response = asyncio.run(backend.generate("hello"))

    assert response.text == "hello from nvidia"
    assert captured["json"]["model"] == "deepseek-ai/deepseek-v4-flash"
    assert captured["json"]["reasoning_effort"] == "max"


def test_nvidia_backend_handles_invalid_response(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": []}

    monkeypatch.setattr("backends.nvidia.requests.post", lambda *args, **kwargs: FakeResponse())

    backend = NvidiaDeepSeekBackend()
    response = asyncio.run(backend.generate("hello"))

    assert response.text.startswith("[nvidia]")
    assert backend.get_status()["status"] == "ERROR"
