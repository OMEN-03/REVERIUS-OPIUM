from plugins.plugin_loader import discover_plugins, initialize_plugins, dispatch_command


def test_plugin_discovery_and_dispatch():
    plugins = discover_plugins()
    assert any(name == "assistant" for name, _ in plugins)

    initialized = initialize_plugins()
    assert "assistant" in initialized

    assert dispatch_command("assistant") is True
