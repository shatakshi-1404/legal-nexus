# Architecture
Modular monolith: FastAPI API -> service layer -> SQLAlchemy -> PostgreSQL (+pgvector). Celery/Redis workers
run ingestion and the LangGraph analysis. React SPA talks to `/api/v1`.

## Agents (LangGraph, `backend/app/workflows/graph.py`)
START -> supervisor -> document -> clause -> legal_rag --(weak evidence, <2 tries)--> legal_rag
legal_rag -> [risk || compliance] (parallel) -> explain -> critic --(>40% rejected, 1 loop)--> legal_rag
critic -> [interrupt if REQUIRE_APPROVAL] -> finalize -> END

The supervisor is a deterministic router (plan node + routing functions), not an LLM worker. LLM calls
happen only in document, clause, legal_rag (query rewrite), risk, compliance and explain. The critic's
verification is deterministic: a cited excerpt must literally appear in the retrieved source text.

## Checkpointing / approval
`PostgresSaver` stores state per analysis (thread_id = analysis id). `POST /analysis/{id}/approve` and
`/resume` re-invoke the graph with `None` input to continue from the last checkpoint.

## Security
Every user-document query filters `owner_id` (see `retrieval/hybrid.py`, `db/repositories/access.py`).
Foreign users get 404. Agent I/O stored for the monitor is truncated and PII-redacted (`core/redact.py`).
