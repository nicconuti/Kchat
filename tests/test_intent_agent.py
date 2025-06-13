from agents.context import AgentContext
from agents.intent_agent import run


def test_intent_agent(monkeypatch):
    monkeypatch.setattr("agents.intent_agent.detect_intent", lambda text: "quote_request")
    ctx = AgentContext(user_id="u", session_id="s", input="price?")
    run(ctx)
    assert ctx.intent == "quote_request"
    assert ctx.confidence == 1.0
