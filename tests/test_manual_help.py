from modules import command_processing


def test_help_command_shows_manual_entries(monkeypatch, capsys):
    captured = []

    def fake_terminal_print(message, color=None):
        captured.append((message, color))

    monkeypatch.setattr(command_processing, "terminal_print", fake_terminal_print)

    command_processing.process_command("help")

    joined = "\n".join(message for message, _ in captured)
    assert "MANUAL" in joined
    assert "help" in joined
    assert "status" in joined


def test_lzbr_salva_command_shows_manual(monkeypatch):
    captured = []

    def fake_terminal_print(message, color=None):
        captured.append((message, color))

    monkeypatch.setattr(command_processing, "terminal_print", fake_terminal_print)

    command_processing.process_command("lzbr salva")

    joined = "\n".join(message for message, _ in captured)
    assert "MANUAL" in joined
    assert "status" in joined
