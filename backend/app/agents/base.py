"""Shared agent plumbing: state schema + @tracked decorator that records every run (redacted)."""
import functools
import time
import uuid
from typing import TypedDict

from app.core.redact import summarize
from app.db.models import AgentRun, WorkflowCheckpoint
from app.db.session import SessionLocal


class State(TypedDict, total=False):
    analysis_id: str
    document_id: str
    owner_id: str
    plan: list[str]
    doc_info: dict
    clauses: list[dict]        # {id, ref, heading, text, page, type}
    evidence: dict             # clause_ref -> [Hit dicts]
    weak_refs: list[str]       # clauses whose evidence is insufficient
    retrieval_attempts: int
    risks: list[dict]
    compliance: list[dict]
    explanations: dict         # clause_ref -> {plain_language, questions}
    findings: list[dict]
    loop_refs: list[str]
    critic_loops: int
    stats: dict
    report: dict


def tracked(agent: str, tools: list[str] | None = None):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(state: State):
            t0 = time.time()
            with SessionLocal() as s:
                run = AgentRun(analysis_id=uuid.UUID(state["analysis_id"]), agent=agent,
                               status="running", tools=tools or [],
                               input=summarize({k: v for k, v in state.items()
                                                if k not in ("analysis_id", "owner_id")}))
                s.add(run)
                s.commit()
                run_id = run.id
            try:
                out = fn(state)
            except Exception as e:
                with SessionLocal() as s:
                    r = s.get(AgentRun, run_id)
                    r.status, r.error = "failed", str(e)[:500]
                    r.duration_ms = int((time.time() - t0) * 1000)
                    s.commit()
                raise
            with SessionLocal() as s:
                r = s.get(AgentRun, run_id)
                r.status, r.output = "completed", summarize(out)
                r.duration_ms = int((time.time() - t0) * 1000)
                s.add(WorkflowCheckpoint(analysis_id=r.analysis_id, thread_id=state["analysis_id"], step=agent))
                s.commit()
            return out
        return wrapper
    return deco
