from agents.context import AgentContext
from agents.embedding_ingestor_agent import run


def test_embedding_ingestor_agent():
    ctx = AgentContext(user_id="u", session_id="s", input="file")
    run(ctx, "dummy.txt")
    assert len(ctx.documents) >= 1

