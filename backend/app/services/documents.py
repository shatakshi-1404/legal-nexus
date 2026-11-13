import os
import uuid
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Clause, Document, DocumentChunk, DocumentPage, User
from app.db.session import SessionLocal
from app.embeddings.embedder import embed_documents
from app.ingestion.chunker import chunk_segments, segment_clauses
from app.ingestion.parser import parse_file

MAGIC = {"pdf": b"%PDF", "docx": b"PK"}


def create_document(db: Session, user: User, filename: str, data: bytes) -> Document:
    s = get_settings()
    safe = Path(filename or "upload").name
    ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else ""
    if ext not in MAGIC:
        raise HTTPException(415, "Only PDF and DOCX files are supported")
    if len(data) > s.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {s.max_upload_mb} MB")
    if not data.startswith(MAGIC[ext]):
        raise HTTPException(400, "File content does not match its extension")
    folder = Path(s.storage_dir) / str(user.id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4()}.{ext}"
    path.write_bytes(data)
    doc = Document(owner_id=user.id, org_id=user.org_id, filename=safe, file_type=ext, storage_path=str(path))
    db.add(doc)
    db.commit()
    return doc


def delete_document(db: Session, doc: Document) -> None:
    try:
        os.remove(doc.storage_path)
    except OSError:
        pass
    db.delete(doc)  # FK ON DELETE CASCADE removes pages, clauses, chunks, analyses, findings
    db.commit()


def ingest_document(doc_id: str) -> None:
    """Worker task: parse -> OCR fallback -> clause segmentation -> chunk -> embed -> pgvector."""
    with SessionLocal() as s:
        doc = s.get(Document, uuid.UUID(doc_id))
        try:
            doc.status = "processing"
            s.commit()
            pages = parse_file(doc.storage_path, doc.file_type)
            for p in pages:
                s.add(DocumentPage(document_id=doc.id, page_number=p.page, text=p.text, is_ocr=p.ocr))
            segs = segment_clauses([(p.page, p.text) for p in pages])
            ref_id = {}
            for seg in segs:
                c = Clause(document_id=doc.id, owner_id=doc.owner_id, clause_ref=seg.ref, heading=seg.heading,
                           text=seg.text, page=seg.page, order_idx=seg.idx)
                s.add(c)
                s.flush()
                ref_id[seg.ref] = c.id
            chunks = chunk_segments(segs)
            vecs = embed_documents([c.text for c in chunks])
            for ch, v in zip(chunks, vecs):
                s.add(DocumentChunk(document_id=doc.id, owner_id=doc.owner_id, org_id=doc.org_id,
                                    clause_id=ref_id[ch.clause_ref], clause_ref=ch.clause_ref,
                                    page=ch.page, text=ch.text, embedding=v))
            doc.num_pages, doc.status = len(pages), "ready"
            s.commit()
        except Exception as e:
            s.rollback()
            doc = s.get(Document, uuid.UUID(doc_id))
            doc.status, doc.error = "failed", str(e)[:500]
            s.commit()
