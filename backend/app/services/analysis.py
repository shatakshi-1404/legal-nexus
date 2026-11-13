import logging
import uuid
from contextlib import ExitStack
from datetime import datetime, timezone

from app.core.config import get_settings
from app.db.models import Analysis
from app.db.session import SessionLocal
from app.workflows.graph import build_graph

log = logging.getLogger(__name__)


def _checkpointer(stack: ExitStack):
    """Postgres checkpointer (resumable across processes); falls back to in-memory with a warning."""
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        saver = stack.enter_context(PostgresSaver.from_conn_string(get_settings().checkpoint_dsn))
        saver.setup()
        return saver
    except Exception as e:
        from langgraph.checkpoint.memory import MemorySaver
        log.warning("Postgres checkpointer unavailable (%s); using in-memory (NOT resumable)", e)
        return MemorySaver()


def run_analysis(analysis_id: str, resume: bool = False) -> None:
    """Start, resume after a crash, or continue after human approval (all share the same thread_id)."""
    with SessionLocal() as db:
        a = db.get(Analysis, uuid.UUID(analysis_id))
        a.status, a.error = "running", None
        db.commit()
        init = None if resume else {"analysis_id": analysis_id, "document_id": str(a.document_id),
                                    "owner_id": str(a.owner_id)}
    try:
        with ExitStack() as stack:
            graph = build_graph(_checkpointer(stack))
            cfg = {"configurable": {"thread_id": analysis_id}}
            graph.invoke(init, cfg)
            awaiting = bool(graph.get_state(cfg).next)
        if awaiting:
            with SessionLocal() as db:
                db.get(Analysis, uuid.UUID(analysis_id)).status = "awaiting_approval"
                db.commit()
    except Exception as e:
        log.exception("analysis failed")
        with SessionLocal() as db:
            a = db.get(Analysis, uuid.UUID(analysis_id))
            a.status, a.error, a.completed_at = "failed", str(e)[:500], datetime.now(timezone.utc)
            db.commit()
