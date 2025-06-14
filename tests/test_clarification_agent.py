from pathlib import Path
from agents.context import AgentContext
from agents.clarification_agent import run


def test_clarification_agent(monkeypatch):
    monkeypatch.setattr(
        "agents.clarification_agent.generate_contextual_question",
        lambda ctx: "what do you mean?",
    )
    monkeypatch.setattr(
        "agents.clarification_agent.generate_fallback_question",
        lambda text: "should not be used",
    )
    monkeypatch.setattr("agents.clarification_agent.HISTORY_FILE", Path("/tmp/empty.log"))
    Path("/tmp/empty.log").write_text("")
    ctx = AgentContext(user_id="u", session_id="s", input="hi")
    run(ctx)
    assert ctx.response == "what do you mean?"
    assert ctx.clarification_attempted is True


def test_clarification_formal(monkeypatch):
    monkeypatch.setattr(
        "agents.clarification_agent.generate_contextual_question",
        lambda ctx: "pu\u00f2 chiarire?",
    )
    ctx = AgentContext(user_id="u", session_id="s", input="hi", formality="formal")
    run(ctx)
    assert ctx.response.startswith("Gentile utente")


def test_clarification_dynamic(monkeypatch, tmp_path):
    log = tmp_path / "clarification_log.log"
    log.write_text("a?\na?\nb?\n")
    monkeypatch.setattr("agents.clarification_agent.HISTORY_FILE", log)
    monkeypatch.setattr(
        "agents.clarification_agent.generate_contextual_question",
        lambda ctx: "dynamic",
    )
    monkeypatch.setattr(
        "agents.clarification_agent.generate_fallback_question",
        lambda text: "unused",
    )
    ctx = AgentContext(user_id="u", session_id="s", input="hi")
    run(ctx)
    assert ctx.response == "dynamic"


def test_clarification_fallback_to_history(monkeypatch, tmp_path):
    log = tmp_path / "clarification_log.log"
    log.write_text("hist?\nhist?\n")
    monkeypatch.setattr("agents.clarification_agent.HISTORY_FILE", log)

    def raise_ctx(ctx):
        raise RuntimeError("fail")

    monkeypatch.setattr(
        "agents.clarification_agent.generate_contextual_question", raise_ctx
    )
    monkeypatch.setattr(
        "agents.clarification_agent.generate_fallback_question", raise_ctx
    )
    ctx = AgentContext(user_id="u", session_id="s", input="hi")
    run(ctx)
    assert ctx.response == "hist?"


def test_contextual_prompt_includes_history(monkeypatch):
    captured = {}

    def fake_call(prompt: str) -> str:
        captured["prompt"] = prompt
        return "sure?"

    monkeypatch.setattr("clarification_prompt.call_mistral", fake_call)
    ctx = AgentContext(
        user_id="u",
        session_id="s",
        input="next",
        conversation_history=[("user", "first"), ("assistant", "what?")],
    )
    run(ctx)
    assert "first" in captured["prompt"]
    assert ctx.response == "sure?"
