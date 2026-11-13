# LegalNexus - Multi-Agent Legal Document Intelligence

FastAPI + LangGraph + PostgreSQL/pgvector + React. Analyzes Indian-law contracts, retrieves legal sources,
flags risky clauses and produces evidence-verified reports. **Analysis support, not legal advice.**

## Quick start (Docker)
```bash
cp .env.example .env            # set GROQ_API_KEY, SECRET_KEY, ADMIN_EMAILS
docker compose -f infrastructure/docker-compose.yml --env-file .env up --build
# load the SAMPLE legal knowledge base (replace with verified sources before real use):
docker compose -f infrastructure/docker-compose.yml exec backend python -m app.scripts.ingest_legal /kb/sources/sample_india.json
```
App: http://localhost:8080 - API docs: http://localhost:8000/docs

## Local dev (no Docker for the app)
```bash
# Postgres with pgvector + Redis must be running (or: docker compose up db redis)
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cp ../.env.example .env && CELERY_EAGER=true uvicorn app.main:app --reload      # CELERY_EAGER runs jobs inline
python -m app.scripts.ingest_legal ../knowledge_base/sources/sample_india.json
cd ../frontend && npm install && npm run dev                                    # http://localhost:5173
```
Tests: `cd backend && pytest tests/unit tests/workflows` (no DB/LLM needed). Needs Tesseract installed for OCR.

## Implementation status (be honest in interviews and on your resume)
| Area | Status |
|---|---|
| Auth (JWT+Argon2), ownership checks, audit log | Implemented |
| PDF/DOCX parsing, OCR fallback, clause segmentation, chunking, embeddings, pgvector | Implemented, untested on real contracts |
| Hybrid retrieval (dense+FTS+RRF+cross-encoder), query rewrite/decomposition | Implemented, not benchmarked |
| 7 agents + supervisor routing, parallel risk/compliance, retrieval retries, critic loop | Implemented, needs a live Groq key to run |
| Deterministic citation verification | Implemented + unit-tested |
| Postgres checkpointing, human approval, resume | Implemented; verify against your installed langgraph version |
| Celery/Redis jobs, SSE stream, report JSON/Markdown | Implemented |
| React UI: dashboard, documents, analysis + agent monitor, chat | Basic version |
| PDF viewer with highlighted clauses (PDF.js), MinIO storage, rate limiting, RBAC beyond admin/user | NOT implemented |
| RAGAS/DeepEval, agent evaluation, contract comparison, V3 extras | NOT implemented (retrieval harness only) |
| Alembic migrations | Configured; generate the first revision yourself |
| Legal knowledge | 6 SAMPLE paraphrased sections only - replace with verified sources |

Known first-run issues to expect: library API drift (langgraph, langfuse), model download time on first embed,
and tuning `MIN_RERANK_SCORE`. Treat this as a strong starting point to run, debug and extend - not a finished product.
