from __future__ import annotations

import asyncio
import logging
from typing import Any

from backends.backend_manager import BackendManager
from backends.registry import BackendRegistry

logger = logging.getLogger(__name__)

_backend_manager: BackendManager | None = None


def _get_backend_manager() -> BackendManager:
    """Get the shared backend manager instance."""
    global _backend_manager
    if _backend_manager is None:
        registry = BackendRegistry()
        from backends.direct_api import DirectAPIBackend
        from backends.local_llm import LocalLLMBackend
        from backends.offline import OfflineBackend
        from backends.openjarvis import OpenJarvisBackend
        from backends.nvidia import NvidiaDeepSeekBackend

        registry.register(OpenJarvisBackend())
        registry.register(LocalLLMBackend())
        registry.register(DirectAPIBackend())
        registry.register(NvidiaDeepSeekBackend())
        registry.register(OfflineBackend())
        _backend_manager = BackendManager(registry=registry)
    return _backend_manager


def get_shared_backend_manager() -> BackendManager:
    """Return the singleton backend manager shared across the application."""
    return _get_backend_manager()


def get_backend_info() -> dict[str, Any]:
    """Return detailed backend telemetry and health status."""
    manager = _get_backend_manager()
    try:
        if not manager._initialized:
            asyncio.run(manager.initialize())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(manager.initialize())
        finally:
            loop.close()
    backend = manager.current_backend
    info = {
        "name": "Offline",
        "status": "Offline",
        "configured": False,
        "model": None,
        "reasoning_effort": None,
        "latency_ms": 0,
        "request_count": 0,
        "error": None,
    }
    if backend is None:
        return info
    info["name"] = getattr(backend, "name", "Offline")
    if getattr(backend, "get_status", None):
        try:
            backend_status = backend.get_status()
            if isinstance(backend_status, dict):
                return backend_status
        except Exception:
            pass
    info["status"] = "ONLINE" if manager._initialized else "UNKNOWN"
    return info


def init_plugin():
    """Register the assistant backend with the plugin loader."""
    return True


def handle_command(command, context=None):
    """Handle assistant-oriented commands in a lightweight way."""
    if command in {"assistant", "assistant chat", "help"}:
        return True
    return False

async def _async_query_ai(prompt: str, temperature: float = 0.5, max_tokens: int = 1024) -> str:
    """Query the configured backend asynchronously."""
    manager = _get_backend_manager()
    await manager.initialize()
    response = await manager.generate(prompt, temperature=temperature, max_tokens=max_tokens)
    return response.text


def query_ai(prompt: str, temperature: float = 0.5, max_tokens: int = 1024) -> str:
    """Compatibility wrapper for AI queries."""
    try:
        return asyncio.run(_async_query_ai(prompt, temperature=temperature, max_tokens=max_tokens))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_async_query_ai(prompt, temperature=temperature, max_tokens=max_tokens))
        finally:
            loop.close()
    except Exception as exc:  # pragma: no cover - defensive path
        logger.error("AI query error", exc_info=exc)
        return f"[ERROR] {str(exc)[:100]}"


def get_backend_status() -> str:
    """Return the currently selected backend name, or Offline if none are available."""
    try:
        manager = _get_backend_manager()
        if manager._initialized and manager.current_backend is not None:
            return manager.current_backend.name
        try:
            asyncio.run(manager.initialize())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(manager.initialize())
            finally:
                loop.close()
        return manager.current_backend.name if manager.current_backend is not None else "Offline"
    except Exception:
        return "Offline"


# =========================================================
# SENTIMENT ANALYSIS
# =========================================================

def analyze_sentiment(text):
    """Simple sentiment analysis."""
    positive = ["good", "great", "excellent", "love", "happy", "awesome", "amazing", "perfect"]
    negative = ["bad", "hate", "terrible", "sad", "angry", "awful", "worst", "horrible"]
    
    text_lower = text.lower()
    pos_count = sum(1 for word in positive if word in text_lower)
    neg_count = sum(1 for word in negative if word in text_lower)
    
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


# =========================================================
# REAL-TIME DATA FETCHER
# =========================================================

def get_weather(city="New York"):
    """Fetch current weather (free API)."""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=5)
        data = response.json()
        current = data["current_condition"][0]
        return f"{current['temp_C']}Â°C, {current['weatherDesc'][0]['value']}"
    except Exception:
        return "Weather data unavailable"


def get_crypto_price(symbol="BTC"):
    """Fetch cryptocurrency prices."""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        data = response.json()
        price = data.get(symbol.lower(), {}).get("usd", "N/A")
        return f"{symbol} = ${price}"
    except Exception:
        return f"{symbol} price unavailable"


def get_news_headlines():
    """Fetch trending news headlines."""
    try:
        url = "https://newsapi.org/v2/top-headlines?country=us&sortBy=popularity&apiKey=demo"
        response = requests.get(url, timeout=5)
        data = response.json()
        headlines = [article["title"] for article in data.get("articles", [])[:3]]
        return headlines
    except Exception:
        return ["News unavailable"]


# =========================================================
# AI CODE GENERATOR
# =========================================================

def is_quota_error(error):
    """Detect if error is API quota/billing error."""
    error_str = str(error).lower()
    quota_indicators = ["429", "insufficient_quota", "quota", "billing", "credit", "plan", "rate_limit_exceeded"]
    return any(indicator in error_str for indicator in quota_indicators)


def get_quota_error_message():
    """Return helpful message for quota errors."""
    return (
        "# API QUOTA ERROR\n"
        "# Your OpenAI API account has reached its usage limit or has billing issues.\n"
        "# \n"
        "# FIX:\n"
        "# 1. Check your OpenAI billing: https://platform.openai.com/account/billing/overview\n"
        "# 2. Add payment method or upgrade plan\n"
        "# 3. Check your API usage limits: https://platform.openai.com/account/billing/limits\n"
        "# 4. Try again after resolving billing issues\n"
        "# \n"
        "# For now, use DEMO MODE: Set demo_mode=True in the code to use fallback responses."
    )


def generate_code(prompt):
    """Generate Python code using AI backend with error handling."""
    try:
        system_context = (
            "You are REVERIUS OPIUM AI, adaptive intelligence. "
            "Generate only clean executable Python code. No markdown."
        )
        full_prompt = f"{system_context}\n\nRequest: {prompt}"
        
        code = query_ai(full_prompt, temperature=0.4, max_tokens=2048)
        
        # Remove markdown if present
        code = code.replace("```python", "").replace("```", "")
        return code.strip()
    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        return f"# ERROR: {str(e)[:100]}"
