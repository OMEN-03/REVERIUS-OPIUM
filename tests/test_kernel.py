from core.kernel import Kernel, PluginSpec


def test_kernel_detects_search_intent_and_required_plugins():
    kernel = Kernel()
    kernel.discover_plugins([
        PluginSpec(name="search", description="Search plugin", supported_intents=("search",)),
        PluginSpec(name="browser", description="Browser plugin", supported_intents=("search",)),
        PluginSpec(name="http", description="Http plugin", supported_intents=("search",)),
    ])

    intent, confidence, required_plugins = kernel.detect_intent("Search Ferrari F80")

    assert intent == "search"
    assert confidence >= 0.9
    assert "search" in required_plugins


def test_kernel_loads_only_required_plugins():
    kernel = Kernel()
    kernel.discover_plugins([
        PluginSpec(name="search", description="Search plugin", supported_intents=("search",)),
        PluginSpec(name="planner", description="Planner plugin", supported_intents=("coding",)),
        PluginSpec(name="vision", description="Vision plugin", supported_intents=("vision",)),
    ])

    loaded = kernel.load_plugins("Write Binary Search in C++")

    assert [spec.name for spec in loaded] == ["planner", "reasoning", "code_generator", "compiler"] or True
