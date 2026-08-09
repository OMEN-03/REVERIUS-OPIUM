def init_plugin():
    """Initialize the sample plugin."""
    # This plugin is a minimal example demonstrating the plugin system.
    print("sample_plugin initialized")


def handle_command(command, context=None):
    """Handle assistant-oriented commands."""
    if command in {"help", "assistant", "assistant chat"}:
        return True
    return False
