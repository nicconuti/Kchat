from agents.context import AgentContext
from agents.response_agent import run


def test_response_agent(monkeypatch):
    monkeypatch.setattr(
        "agents.response_agent.generate_response",
        lambda user_input, intent, lang: "hi",
    )
    ctx = AgentContext(user_id="u", session_id="s", input="hello", intent="greet", formality="formal")
    run(ctx)
    assert ctx.response == "hi"


def test_response_doc_mode():
    ctx = AgentContext(
        user_id="u", session_id="s", input="hello", intent="info", documents=["d"], formality="formal"
    )
    run(ctx)
    assert ctx.response.startswith("[formal]")


def test_response_action_mode(monkeypatch):
    monkeypatch.setattr(
        "agents.response_agent.generate_response",
        lambda user_input, intent, lang: "unused",
    )
    monkeypatch.setattr("agents.response_agent.action_run", lambda ctx: ctx)
    ctx = AgentContext(user_id="u", session_id="s", input="hello", intent="open_ticket", formality="informal")
    run(ctx)
    assert "Action taken" in ctx.response


def test_response_history(monkeypatch):
    captured = {}

    def fake_generate(user_input: str, intent: str, lang: str) -> str:
        captured["input"] = user_input
        return "ok"

    monkeypatch.setattr("agents.response_agent.generate_response", fake_generate)
    ctx = AgentContext(
        user_id="u",
        session_id="s",
        input="again",
        intent="chat",
        conversation_history=[("user", "hi"), ("assistant", "hello")],
    )
    run(ctx)
    assert "hi" in captured["input"]

