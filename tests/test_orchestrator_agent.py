import json
from agents.context import AgentContext
import agents.orchestrator_agent as orchestrator
from agents.orchestrator_agent import run


def _common_patches(monkeypatch):
    monkeypatch.setattr("agents.orchestrator_agent.detect_language", lambda ctx: ctx)
    monkeypatch.setattr(
        "agents.orchestrator_agent.detect_intent",
        lambda ctx: setattr(ctx, "intent", "ok") or ctx,
    )
    monkeypatch.setattr("agents.orchestrator_agent.generate_response", lambda ctx: setattr(ctx, "response", "ok") or ctx)
    monkeypatch.setattr("agents.orchestrator_agent.translate", lambda ctx, lang, style="neutral": ctx)
    monkeypatch.setattr("agents.orchestrator_agent.translate_text", lambda text, target_lang="en": text)
    monkeypatch.setattr("agents.orchestrator_agent.clarify", lambda ctx: ctx)
    orchestrator._STEP_MAP["respond"] = orchestrator.generate_response
    orchestrator._STEP_MAP["language"] = orchestrator.detect_language
    orchestrator._STEP_MAP["intent"] = orchestrator.detect_intent


def test_orchestrator_sequence_quote(monkeypatch):
    _common_patches(monkeypatch)
    called = {"r": 0}
    monkeypatch.setattr("agents.orchestrator_agent.retrieve", lambda ctx, query=None: called.__setitem__("r", called["r"] + 1) or ctx)
    orchestrator._STEP_MAP["retrieve"] = orchestrator.retrieve

    def fake_call(prompt: str) -> str:
        return json.dumps({"reasoning": "quote", "sequence": ["language", "intent", "retrieve", "respond"]})

    monkeypatch.setattr("agents.orchestrator_agent.call_mistral", fake_call)
    monkeypatch.setattr("agents.orchestrator_agent.verify", lambda ctx: True)

    ctx = AgentContext(user_id="u", session_id="s", input="price?")
    run(ctx)
    assert ctx.reasoning_trace == "quote"
    assert called["r"] == 1
    assert ctx.response == "ok"
    assert ctx.conversation_history == [("user", "price?"), ("assistant", "ok")]


def test_orchestrator_sequence_smalltalk(monkeypatch):
    _common_patches(monkeypatch)
    called = {"r": 0}
    monkeypatch.setattr("agents.orchestrator_agent.retrieve", lambda ctx, query=None: called.__setitem__("r", called["r"] + 1) or ctx)
    orchestrator._STEP_MAP["retrieve"] = orchestrator.retrieve

    def fake_call(prompt: str) -> str:
        return json.dumps({"reasoning": "chat", "sequence": ["language", "intent", "respond"]})

    monkeypatch.setattr("agents.orchestrator_agent.call_mistral", fake_call)
    monkeypatch.setattr("agents.orchestrator_agent.verify", lambda ctx: True)

    ctx = AgentContext(user_id="u", session_id="s", input="hello")
    run(ctx)
    assert ctx.reasoning_trace == "chat"
    assert called["r"] == 0
    assert ctx.response == "ok"
    assert ctx.conversation_history == [("user", "hello"), ("assistant", "ok")]


def test_translation_before_intent(monkeypatch):
    called = {"text": None}

    def fake_translate(text: str, target_lang: str = "en"):
        called["text"] = text + "-en"
        return called["text"]

    def fake_detect_intent(ctx):
        called["intent_input"] = ctx.input
        ctx.intent = "ok"
        return ctx

    _common_patches(monkeypatch)
    monkeypatch.setattr("agents.orchestrator_agent.translate_text", fake_translate)
    monkeypatch.setattr("agents.orchestrator_agent.detect_language", lambda ctx: setattr(ctx, "language", "fr") or ctx)
    orchestrator._STEP_MAP["language"] = orchestrator.detect_language
    monkeypatch.setattr("agents.orchestrator_agent.detect_intent", fake_detect_intent)
    orchestrator._STEP_MAP["intent"] = orchestrator.detect_intent
    monkeypatch.setattr("agents.orchestrator_agent.verify", lambda ctx: True)

    ctx = AgentContext(user_id="u", session_id="s", input="bonjour")
    run(ctx)
    assert called["intent_input"] == "bonjour-en"
    assert ctx.conversation_history == [("user", "bonjour"), ("assistant", "ok")]


def test_conversation_history_grows(monkeypatch):
    _common_patches(monkeypatch)
    monkeypatch.setattr("agents.orchestrator_agent.verify", lambda ctx: True)
    ctx = AgentContext(user_id="u", session_id="s", input="hi")
    run(ctx)
    ctx.input = "again"
    run(ctx)
    assert ctx.conversation_history == [
        ("user", "hi"),
        ("assistant", "ok"),
        ("user", "again"),
        ("assistant", "ok"),
    ]
