from agents.context import AgentContext
from agents.language_agent import run


def test_language_agent(monkeypatch):
    monkeypatch.setattr("agents.language_agent.detect_language", lambda text: "it")
    ctx = AgentContext(user_id="u", session_id="s", input="ciao")
    run(ctx)
    assert ctx.language == "it"
    assert ctx.formality == "informal"


def test_language_agent_speech(monkeypatch):
    monkeypatch.setattr("agents.language_agent.detect_language", lambda text: "it")
    monkeypatch.setattr("agents.language_agent.speech_to_text", lambda path: "ciao")
    ctx = AgentContext(user_id="u", session_id="s", input="audio.wav")
    run(ctx)
    assert ctx.input == "ciao"


def test_language_agent_mixed(monkeypatch):
    monkeypatch.setattr("agents.language_agent.detect_language", lambda text: "en")
    ctx = AgentContext(user_id="u", session_id="s", input="hello ciao")
    run(ctx)
    assert ctx.mixed_language is True
