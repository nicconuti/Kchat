from agents.context import AgentContext
import agents.orchestrator_agent as orchestrator
from agents.orchestrator_agent import run


def test_orchestrator_agent(monkeypatch):
    monkeypatch.setattr("agents.orchestrator_agent.detect_language", lambda ctx: ctx.language)
    monkeypatch.setattr(
        "agents.orchestrator_agent.detect_intent",
        lambda ctx: setattr(ctx, "intent", "greet") or ctx,
    )
    monkeypatch.setattr(
        "agents.orchestrator_agent.retrieve",
        lambda ctx, query=None: ctx,
    )
    monkeypatch.setattr(
        "agents.orchestrator_agent.generate_response",
        lambda ctx: setattr(ctx, "response", "ok") or ctx,
    )
    monkeypatch.setattr("agents.orchestrator_agent.clarify", lambda ctx: ctx)
    monkeypatch.setattr(
        "agents.orchestrator_agent.translate", lambda ctx, lang, style="neutral": ctx
    )
    monkeypatch.setattr("agents.orchestrator_agent.verify", lambda ctx: True)
    monkeypatch.setattr(
        "agents.orchestrator_agent.choose_agent_sequence",
        lambda ctx: (
            setattr(ctx, "reasoning_trace", "patched")
            or [
                orchestrator.detect_language,
                orchestrator.detect_intent,
                orchestrator.retrieve,
                orchestrator.generate_response,
            ]
        ),
    )
    ctx = AgentContext(user_id="u", session_id="s", input="hi")
    run(ctx)
    assert ctx.response == "ok"
    assert ctx.reasoning_trace

