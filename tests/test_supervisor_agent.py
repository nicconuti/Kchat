from agents.context import AgentContext
from agents.supervisor_agent import run


def test_supervisor_agent(tmp_path, monkeypatch):
    log_dir = tmp_path
    (log_dir / "intent_log.log").write_text("unclear\n")
    (log_dir / "validation_log.log").write_text("invalid\n")
    monkeypatch.setattr(
        "agents.supervisor_agent.LOG_FILES",
        [log_dir / "intent_log.log", log_dir / "validation_log.log"],
    )
    ctx = AgentContext(user_id="u", session_id="s", input="")
    run(ctx)
    assert "intent" in ctx.response
    assert "verification" in ctx.response


def test_supervisor_no_issues(tmp_path, monkeypatch):
    log_dir = tmp_path
    (log_dir / "intent_log.log").write_text("valid\n")
    (log_dir / "validation_log.log").write_text("valid\n")
    monkeypatch.setattr(
        "agents.supervisor_agent.LOG_FILES",
        [log_dir / "intent_log.log", log_dir / "validation_log.log"],
    )
    ctx = AgentContext(user_id="u", session_id="s", input="")
    run(ctx)
    assert ctx.response == "No issues"

