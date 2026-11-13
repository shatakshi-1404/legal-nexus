"""Legal reference knowledge base ingestion (kept separate from user documents)."""
from sqlalchemy.orm import Session

from app.db.models import LegalChunk, LegalSource
from app.embeddings.embedder import embed_documents


def ingest_legal_source(db: Session, meta: dict, sections: list[dict]) -> LegalSource:
    src = LegalSource(title=meta["title"], source_type=meta.get("source_type", "act"),
                      jurisdiction=meta.get("jurisdiction", "IN"), version=meta.get("version", ""),
                      effective_date=meta.get("effective_date", ""), url=meta.get("url", ""),
                      verified=bool(meta.get("verified", False)))
    db.add(src)
    db.flush()
    vecs = embed_documents([s["text"] for s in sections])
    for s, v in zip(sections, vecs):
        db.add(LegalChunk(source_id=src.id, section=s["section"], jurisdiction=src.jurisdiction,
                          text=s["text"], embedding=v))
    db.commit()
    return src
