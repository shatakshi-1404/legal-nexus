"""Hybrid retrieval: dense (pgvector) + sparse (Postgres FTS) -> RRF -> cross-encoder rerank.

SECURITY: user-document searches ALWAYS filter by owner_id. Never call kind="document" without it.
"""
import re
import uuid
from dataclasses import asdict, dataclass, field
from functools import lru_cache

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import DocumentChunk, LegalChunk, LegalSource
from app.embeddings.embedder import embed_query
from app.retrieval.fusion import rrf

MODES = ("dense", "hybrid", "hybrid_rerank")


@dataclass
class Hit:
    id: str
    text: str
    score: float = 0.0
    meta: dict = field(default_factory=dict)

    def asdict(self) -> dict:
        return asdict(self)


@lru_cache
def _reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder(get_settings().reranker_model)


def _or_query(q: str) -> str:
    terms = list(dict.fromkeys(re.findall(r"[A-Za-z0-9]{3,}", q.lower())))[:24]
    return " | ".join(terms)


class HybridRetriever:
    def __init__(self, db: Session):
        self.db = db

    def search(self, query: str, *, kind: str, owner_id: uuid.UUID | None = None,
               document_id: uuid.UUID | None = None, jurisdiction: str = "IN",
               mode: str = "hybrid_rerank", top_k: int = 5, candidates: int = 30) -> list[Hit]:
        assert mode in MODES
        if kind == "document":
            if owner_id is None:
                raise ValueError("owner_id is required for document retrieval")
            model = DocumentChunk
            filters = [DocumentChunk.owner_id == owner_id]
            if document_id:
                filters.append(DocumentChunk.document_id == document_id)
        else:
            model = LegalChunk
            filters = [LegalChunk.jurisdiction == jurisdiction]

        dense = self._dense(model, filters, query, candidates)
        if mode == "dense":
            ids = dense[:top_k]
            return self._hydrate(kind, ids, {i: 1 / (60 + r) for r, i in enumerate(ids, 1)})

        sparse = self._sparse(model, filters, query, candidates)
        fused = rrf([dense, sparse])
        if mode == "hybrid":
            top = fused[:top_k]
            return self._hydrate(kind, [i for i, _ in top], dict(top))

        pool = [i for i, _ in fused[: max(top_k * 3, 15)]]
        hits = self._hydrate(kind, pool, dict(fused))
        if not hits:
            return []
        scores = _reranker().predict([(query, h.text) for h in hits])
        for h, s in zip(hits, scores):
            h.score = float(s)
        return sorted(hits, key=lambda h: h.score, reverse=True)[:top_k]

    def _dense(self, model, filters, query, n) -> list[str]:
        qv = embed_query(query)
        stmt = select(model.id).where(*filters).order_by(model.embedding.cosine_distance(qv)).limit(n)
        return [str(i) for i in self.db.scalars(stmt)]

    def _sparse(self, model, filters, query, n) -> list[str]:
        q = _or_query(query)
        if not q:
            return []
        tsq = func.to_tsquery("english", q)
        tsv = func.to_tsvector("english", model.text)
        stmt = (select(model.id).where(*filters, tsv.op("@@")(tsq))
                .order_by(func.ts_rank_cd(tsv, tsq).desc()).limit(n))
        return [str(i) for i in self.db.scalars(stmt)]

    def _hydrate(self, kind: str, ids: list[str], scores: dict[str, float]) -> list[Hit]:
        if not ids:
            return []
        uids = [uuid.UUID(i) for i in ids]
        out: dict[str, Hit] = {}
        if kind == "legal":
            rows = self.db.execute(
                select(LegalChunk, LegalSource).join(LegalSource, LegalSource.id == LegalChunk.source_id)
                .where(LegalChunk.id.in_(uids))).all()
            for c, s in rows:
                out[str(c.id)] = Hit(str(c.id), c.text, scores.get(str(c.id), 0.0), {
                    "source_id": str(s.id), "source_title": s.title, "section": c.section,
                    "version": s.version, "verified": s.verified})
        else:
            for c in self.db.scalars(select(DocumentChunk).where(DocumentChunk.id.in_(uids))):
                out[str(c.id)] = Hit(str(c.id), c.text, scores.get(str(c.id), 0.0), {
                    "document_id": str(c.document_id), "clause_ref": c.clause_ref, "page": c.page})
        return [out[i] for i in ids if i in out]  # preserve fused order
