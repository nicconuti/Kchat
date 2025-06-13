from agents.context import AgentContext


def test_defaults():
    ctx = AgentContext(user_id="u", session_id="s", input="hi")
    assert ctx.language == "en"
    assert ctx.intent is None
    assert ctx.documents == []
    assert ctx.source_reliability == 0.0
    assert ctx.error_flag is False
    assert ctx.formality is None
    assert ctx.mixed_language is False
    assert ctx.reasoning_trace == ""
