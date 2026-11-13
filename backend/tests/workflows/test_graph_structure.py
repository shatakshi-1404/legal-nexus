import pytest

pytest.importorskip("langgraph")


def test_routing_functions():
    from app.workflows.graph import route_after_critic, route_after_rag
    assert route_after_rag({"weak_refs": ["CL-001"], "retrieval_attempts": 1}) == "legal_rag"
    assert route_after_rag({"weak_refs": ["CL-001"], "retrieval_attempts": 2}) == ["risk", "compliance"]
    assert route_after_rag({"weak_refs": [], "retrieval_attempts": 1}) == ["risk", "compliance"]
    assert route_after_critic({"loop_refs": ["CL-002"]}) == "legal_rag"
    assert route_after_critic({"loop_refs": []}) == "finalize"
