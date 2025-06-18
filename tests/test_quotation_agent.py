from agents.context import AgentContext
from agents.quotation_agent import run


def test_quotation_agent():
    ctx = AgentContext(user_id="u", session_id="s", input="quote")
    run(ctx)
    assert ctx.response is not None
    assert "quote" in ctx.response.lower()
