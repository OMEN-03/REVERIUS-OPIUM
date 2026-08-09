from core.intent.intent_engine import IntentEngine
from core.intent.intent_registry import IntentRegistry


def test_search_intent_detects_synonyms_and_extracts_query():
    engine = IntentEngine()
    result = engine.analyze("Can you search for Python tutorials?")

    assert result.primary_intent is not None
    assert result.primary_intent.name == "search"
    assert result.primary_intent.parameters["query"] == "Python tutorials"
    assert result.primary_intent.confidence >= 0.8


def test_context_aware_search_combines_follow_up_query():
    engine = IntentEngine()
    first = engine.analyze("Search for Python tutorials")
    follow_up = engine.analyze("For beginners", context={"previous_intent": first.primary_intent})

    assert follow_up.primary_intent is not None
    assert follow_up.primary_intent.name == "search"
    assert "for beginners" in follow_up.primary_intent.parameters["query"]


def test_ambiguous_command_requires_confirmation():
    engine = IntentEngine()
    result = engine.analyze("Open it")

    assert result.primary_intent is not None
    assert result.primary_intent.name == "open"
    assert result.primary_intent.requires_confirmation is True


def test_delete_intent_requires_confirmation():
    engine = IntentEngine()
    result = engine.analyze("Delete the old project")

    assert result.primary_intent is not None
    assert result.primary_intent.name == "delete"
    assert result.primary_intent.requires_confirmation is True


def test_multi_intent_command_is_split_into_actions():
    engine = IntentEngine()
    result = engine.analyze("Open Chrome and search for Python tutorials")

    assert len(result.intents) >= 2
    assert {intent.name for intent in result.intents} >= {"open", "search"}


def test_builtin_intents_are_registered_on_engine_init():
    engine = IntentEngine()
    definition = engine.registry.get("search")

    assert definition is not None
    assert definition.name == "search"
    assert "search" in definition.keywords


def test_registry_supports_plugin_style_registration():
    registry = IntentRegistry()

    @registry.register_intent(name="weather", keywords=["weather", "forecast"], risk_level="safe")
    def weather_handler(query: str):
        return query

    definition = registry.get("weather")
    assert definition is not None
    assert definition.name == "weather"
    assert "weather" in definition.keywords


def test_registry_supports_direct_intent_registration():
    registry = IntentRegistry()
    registry.register_intent(name="todo", keywords=["todo", "task"], risk_level="safe")

    definition = registry.get("todo")
    assert definition is not None
    assert definition.name == "todo"
    assert "todo" in definition.keywords
    assert definition.handler is None
