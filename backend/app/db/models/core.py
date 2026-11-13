import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (Boolean, DateTime, ForeignKey, Index, Integer, String, Text,
                        UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

EMB_DIM = 384  # BAAI/bge-small-en-v1.5


def _id():
    return mapped_column(primary_key=True, default=uuid.uuid4)


def _fk(table: str, nullable=False):
    return mapped_column(ForeignKey(f"{table}.id", ondelete="CASCADE"), nullable=nullable, index=True)


def _ts():
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[uuid.UUID] = _id()
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = _ts()


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _id()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200), default="")
    role: Mapped[str] = mapped_column(String(20), default="user")  # user | admin
    org_id: Mapped[uuid.UUID | None] = _fk("organizations", nullable=True)
    created_at: Mapped[datetime] = _ts()


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "org_id"),)
    id: Mapped[uuid.UUID] = _id()
    user_id: Mapped[uuid.UUID] = _fk("users")
    org_id: Mapped[uuid.UUID] = _fk("organizations")
    role: Mapped[str] = mapped_column(String(20), default="member")  # owner | admin | member


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = _id()
    owner_id: Mapped[uuid.UUID] = _fk("users")
    org_id: Mapped[uuid.UUID | None] = _fk("organizations", nullable=True)
    filename: Mapped[str] = mapped_column(String(300))
    file_type: Mapped[str] = mapped_column(String(10))
    storage_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="uploaded")  # uploaded|processing|ready|failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    doc_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    doc_meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    num_pages: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = _ts()


class DocumentPage(Base):
    __tablename__ = "document_pages"
    id: Mapped[uuid.UUID] = _id()
    document_id: Mapped[uuid.UUID] = _fk("documents")
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    is_ocr: Mapped[bool] = mapped_column(Boolean, default=False)


class Clause(Base):
    __tablename__ = "clauses"
    id: Mapped[uuid.UUID] = _id()
    document_id: Mapped[uuid.UUID] = _fk("documents")
    owner_id: Mapped[uuid.UUID] = _fk("users")
    clause_ref: Mapped[str] = mapped_column(String(20))  # CL-001
    heading: Mapped[str] = mapped_column(String(200), default="")
    text: Mapped[str] = mapped_column(Text)
    page: Mapped[int] = mapped_column(Integer, default=1)
    clause_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    order_idx: Mapped[int] = mapped_column(Integer, default=0)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[uuid.UUID] = _id()
    document_id: Mapped[uuid.UUID] = _fk("documents")
    owner_id: Mapped[uuid.UUID] = _fk("users")  # ownership filter on EVERY retrieval query
    org_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    clause_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clauses.id", ondelete="CASCADE"), nullable=True)
    clause_ref: Mapped[str] = mapped_column(String(20), default="")
    page: Mapped[int] = mapped_column(Integer, default=1)
    text: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(EMB_DIM))


class LegalSource(Base):
    __tablename__ = "legal_sources"
    id: Mapped[uuid.UUID] = _id()
    title: Mapped[str] = mapped_column(String(300))
    source_type: Mapped[str] = mapped_column(String(30), default="act")  # act | judgment | reference
    jurisdiction: Mapped[str] = mapped_column(String(10), default="IN")
    version: Mapped[str] = mapped_column(String(50), default="")
    effective_date: Mapped[str] = mapped_column(String(30), default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = _ts()


class LegalChunk(Base):
    __tablename__ = "legal_chunks"
    id: Mapped[uuid.UUID] = _id()
    source_id: Mapped[uuid.UUID] = _fk("legal_sources")
    section: Mapped[str] = mapped_column(String(100), default="")
    jurisdiction: Mapped[str] = mapped_column(String(10), default="IN", index=True)
    text: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(EMB_DIM))


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[uuid.UUID] = _id()
    document_id: Mapped[uuid.UUID] = _fk("documents")
    owner_id: Mapped[uuid.UUID] = _fk("users")
    status: Mapped[str] = mapped_column(String(30), default="queued")
    # queued | running | awaiting_approval | completed | failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = _ts()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Risk(Base):
    __tablename__ = "risks"
    id: Mapped[uuid.UUID] = _id()
    analysis_id: Mapped[uuid.UUID] = _fk("analyses")
    finding_id: Mapped[str] = mapped_column(String(20))
    clause_ref: Mapped[str] = mapped_column(String(20))
    page: Mapped[int] = mapped_column(Integer, default=1)
    category: Mapped[str] = mapped_column(String(60))
    severity: Mapped[str] = mapped_column(String(10))
    rationale: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    questions: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(20))  # verified | flagged | rejected


class ComplianceFinding(Base):
    __tablename__ = "compliance_findings"
    id: Mapped[uuid.UUID] = _id()
    analysis_id: Mapped[uuid.UUID] = _fk("analyses")
    finding_id: Mapped[str] = mapped_column(String(20))
    clause_ref: Mapped[str] = mapped_column(String(20))
    compliance_status: Mapped[str] = mapped_column(String(30))
    rationale: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20))


class Citation(Base):
    __tablename__ = "citations"
    id: Mapped[uuid.UUID] = _id()
    analysis_id: Mapped[uuid.UUID] = _fk("analyses")
    finding_id: Mapped[str] = mapped_column(String(20))
    document_id: Mapped[uuid.UUID] = mapped_column()
    clause_ref: Mapped[str] = mapped_column(String(20))
    document_page: Mapped[int] = mapped_column(Integer, default=1)
    document_excerpt: Mapped[str] = mapped_column(Text)
    legal_source_id: Mapped[str] = mapped_column(String(64), default="")
    legal_section: Mapped[str] = mapped_column(String(100), default="")
    legal_excerpt: Mapped[str] = mapped_column(Text, default="")
    citation_verified: Mapped[bool] = mapped_column(Boolean, default=False)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = _id()
    user_id: Mapped[uuid.UUID] = _fk("users")
    document_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = _ts()


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = _id()
    conversation_id: Mapped[uuid.UUID] = _fk("conversations")
    role: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    sources: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = _ts()


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[uuid.UUID] = _id()
    analysis_id: Mapped[uuid.UUID] = _fk("analyses")
    agent: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="running")
    input: Mapped[dict] = mapped_column(JSONB, default=dict)   # redacted summaries only
    output: Mapped[dict] = mapped_column(JSONB, default=dict)  # redacted summaries only
    tools: Mapped[list] = mapped_column(JSONB, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = _ts()
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class WorkflowCheckpoint(Base):
    """Audit view of workflow progress. Resumable state lives in LangGraph's Postgres checkpointer."""
    __tablename__ = "workflow_checkpoints"
    id: Mapped[uuid.UUID] = _id()
    analysis_id: Mapped[uuid.UUID] = _fk("analyses")
    thread_id: Mapped[str] = mapped_column(String(64))
    step: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = _ts()


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[uuid.UUID] = _id()
    user_id: Mapped[uuid.UUID] = _fk("users")
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    target_id: Mapped[str] = mapped_column(String(64), default="")  # finding_id / message id
    rating: Mapped[int] = mapped_column(Integer)  # -1 | 1
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = _ts()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = _id()
    user_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    action: Mapped[str] = mapped_column(String(60))
    resource: Mapped[str] = mapped_column(String(100), default="")
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = _ts()


# Indexes: HNSW (cosine) for dense search, GIN for full-text search.
for _m, _n in ((DocumentChunk, "document_chunks"), (LegalChunk, "legal_chunks")):
    Index(f"ix_{_n}_emb_hnsw", _m.embedding, postgresql_using="hnsw",
          postgresql_with={"m": 16, "ef_construction": 64},
          postgresql_ops={"embedding": "vector_cosine_ops"})
    Index(f"ix_{_n}_fts", func.to_tsvector("english", _m.text), postgresql_using="gin")
