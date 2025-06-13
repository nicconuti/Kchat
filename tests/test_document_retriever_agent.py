from agents.context import AgentContext
from agents.document_retriever_agent import run


def test_document_retriever_agent():
    ctx = AgentContext(user_id="u", session_id="s", role="user", input="manual")
    run(ctx)
    assert len(ctx.documents) == 2
    assert ctx.source_reliability == 0.9


def test_document_retriever_permission_denied():
    ctx = AgentContext(user_id="g", session_id="s", role="guest", input="manual")
    run(ctx)
    assert ctx.error_flag is True
    assert ctx.documents == []


def test_admin_access_setup():
    ctx = AgentContext(user_id="a", session_id="s", role="admin", input="setup")
    run(ctx)
    assert ctx.documents == ["setup guide"]
