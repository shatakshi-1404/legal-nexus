"""LLM-based query rewriting and decomposition. Both fail safe to the original query."""
import logging

from app.core import llm
from app.prompts import templates as P
from app.schemas.agents import Queries, Rewritten

log = logging.getLogger(__name__)


def rewrite_query(query: str) -> str:
    try:
        return llm.structured(Rewritten, P.QUERY_REWRITE, query).query or query
    except Exception as e:
        log.warning("rewrite failed: %s", e)
        return query


def decompose(question: str) -> list[str]:
    try:
        qs = llm.structured(Queries, P.DECOMPOSE, question).queries
        return [q for q in qs if q.strip()][:3] or [question]
    except Exception as e:
        log.warning("decompose failed: %s", e)
        return [question]
