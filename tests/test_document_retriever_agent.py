from agents.context import AgentContext
from agents.document_retriever_agent import run


def test_document_retriever_agent():
    ctx = AgentContext(user_id="u", session_id="s", input="manual")
    run(ctx)
    assert len(ctx.documents) == 2
    assert ctx.source_reliability == 0.9


def test_document_retriever_permission_denied():
    ctx = AgentContext(user_id="guest", session_id="s", input="manual")
    run(ctx)
    assert ctx.error_flag is True
    assert ctx.documents == []
