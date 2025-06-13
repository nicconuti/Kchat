from agents.context import AgentContext
from agents.action_agent import run


def test_action_agent():
    ctx = AgentContext(user_id="u", session_id="s", input="do")
    run(ctx)
    assert ctx.intent is None or isinstance(ctx.intent, str)
