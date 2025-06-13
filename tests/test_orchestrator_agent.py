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
    monkeypatch.setattr("agents.orchestrator_agent.clarify", lambda ctx: ctx)
    orchestrator._STEP_MAP["respond"] = orchestrator.generate_response


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
