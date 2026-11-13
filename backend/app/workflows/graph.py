"""LangGraph workflow: supervisor-routed, parallel risk||compliance, retrieval retries, critic loop,
optional human approval (interrupt before finalize), Postgres checkpointing."""
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from app.agents import nodes
from app.agents.base import State
from app.core.config import get_settings


def route_after_rag(state: State):
    """Supervisor routing: retry retrieval while evidence is weak, else fan out in parallel."""
    if state.get("weak_refs") and state.get("retrieval_attempts", 0) < nodes.MAX_RETRIEVAL_ATTEMPTS:
        return "legal_rag"
    return ["risk", "compliance"]


def route_after_critic(state: State):
    """Critic feedback: unsupported findings trigger one more retrieval pass."""
    return "legal_rag" if state.get("loop_refs") else "finalize"


def build_graph(checkpointer=None):
    retry = RetryPolicy(max_attempts=2)
    g = StateGraph(State)
    for name, fn in [("supervisor", nodes.supervisor_plan), ("document", nodes.document_node),
                     ("clause", nodes.clause_node), ("legal_rag", nodes.legal_rag_node),
                     ("risk", nodes.risk_node), ("compliance", nodes.compliance_node),
                     ("explain", nodes.explain_node), ("critic", nodes.critic_node),
                     ("finalize", nodes.finalize_node)]:
        g.add_node(name, fn, retry_policy=retry)  # on older langgraph use retry=
    g.add_edge(START, "supervisor")
    g.add_edge("supervisor", "document")
    g.add_edge("document", "clause")
    g.add_edge("clause", "legal_rag")
    g.add_conditional_edges("legal_rag", route_after_rag, ["legal_rag", "risk", "compliance"])
    g.add_edge(["risk", "compliance"], "explain")  # join: waits for both parallel branches
    g.add_edge("explain", "critic")
    g.add_conditional_edges("critic", route_after_critic, ["legal_rag", "finalize"])
    g.add_edge("finalize", END)
    interrupt = ["finalize"] if get_settings().require_approval else None
    return g.compile(checkpointer=checkpointer, interrupt_before=interrupt)
