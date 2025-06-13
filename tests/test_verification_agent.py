from agents.context import AgentContext
from agents.verification_agent import run


def test_verification_agent(monkeypatch):
    monkeypatch.setattr("agents.verification_agent.verify_response", lambda q, a: True)
    ctx = AgentContext(user_id="u", session_id="s", input="hi", response="reply")
    assert run(ctx) is True


def test_verification_uncertain(monkeypatch):
    calls = iter([True, False, False])
    monkeypatch.setattr("agents.verification_agent.verify_response", lambda q, a: next(calls))
    ctx = AgentContext(user_id="u", session_id="s", input="hi", response="reply")
    assert run(ctx) is False
    assert ctx.error_flag is False

