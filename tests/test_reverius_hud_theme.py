from types import SimpleNamespace

from ui.hud_theme import (
    ReveriusTheme,
    build_dashboard_summary,
    build_operational_snapshot,
    state_to_status,
)


def test_theme_tokens_are_centered():
    assert ReveriusTheme.ACCENT == "#d2a447"
    assert ReveriusTheme.STATUS_COLORS["IDLE"] == ReveriusTheme.MUTED


def test_state_to_status_maps_known_states():
    assert state_to_status("LISTENING") == "LISTENING"
    assert state_to_status("unknown") == "IDLE"


def test_build_dashboard_summary_emphasizes_operational_context():
    module = SimpleNamespace(
        current_personality="JARVIS",
        hud_ai_state="PROCESSING",
        hud_current_task="Reviewing memory",
        memory_entries={"1": {}, "2": {}},
        loaded_plugins=["notes", "vision"],
        jarvis_available=True,
    )

    summary = build_dashboard_summary(module)

    assert summary["personality"] == "JARVIS"
    assert "Reviewing memory" in summary["mission"]
    assert "2 memory entries" in summary["operator_context"]
    assert "2 plugins" in summary["operator_context"]


def test_build_operational_snapshot_collects_runtime_context():
    module = SimpleNamespace(
        current_personality="OMEN",
        hud_ai_state="LISTENING",
        hud_current_task="Listening for commands",
        memory_entries={"1": {}, "2": {}, "3": {}},
        loaded_plugins=["notes"],
        jarvis_available=False,
    )

    snapshot = build_operational_snapshot(module)

    assert snapshot["state"] == "LISTENING"
    assert snapshot["memory_entries"] == 3
    assert snapshot["plugin_count"] == 1
    assert snapshot["context_tags"]
    assert snapshot["pipeline"][0]["label"] == "INPUT"
