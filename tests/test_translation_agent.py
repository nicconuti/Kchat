from agents.context import AgentContext
from agents.translation_agent import run


def test_translation_agent(monkeypatch):
    monkeypatch.setattr("agents.translation_agent.translate", lambda text, target_lang: text + "-es")
    ctx = AgentContext(user_id="u", session_id="s", input="teh book", language="en", response="teh book")
    run(ctx, "es", style="friendly")
    assert ctx.response == "[friendly] the book-es"
    assert ctx.language == "es"
