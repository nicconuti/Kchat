from pathlib import Path
from agents.context import AgentContext
from agents.clarification_agent import run


def test_clarification_agent(monkeypatch):
    monkeypatch.setattr(
        "agents.clarification_agent.generate_fallback_question",
        lambda text: "what do you mean?",
    )
    monkeypatch.setattr("agents.clarification_agent.HISTORY_FILE", Path("/tmp/empty.log"))
    Path("/tmp/empty.log").write_text("")
    ctx = AgentContext(user_id="u", session_id="s", input="hi")
    run(ctx)
    assert ctx.response == "what do you mean?"
    assert ctx.clarification_attempted is True


def test_clarification_formal(monkeypatch):
    monkeypatch.setattr(
        "agents.clarification_agent.generate_fallback_question",
        lambda text: "pu\u00f2 chiarire?",
    )
    ctx = AgentContext(user_id="u", session_id="s", input="hi", formality="formal")
    run(ctx)
    assert ctx.response.startswith("Gentile utente")


def test_clarification_dynamic(monkeypatch, tmp_path):
    log = tmp_path / "clarification_log.log"
    log.write_text("a?\na?\nb?\n")
    monkeypatch.setattr("agents.clarification_agent.HISTORY_FILE", log)
    monkeypatch.setattr(
        "agents.clarification_agent.generate_fallback_question",
        lambda text: "unused",
    )
    ctx = AgentContext(user_id="u", session_id="s", input="hi")
    run(ctx)
    assert ctx.response == "a?"
