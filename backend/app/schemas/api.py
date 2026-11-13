import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    filename: str
    file_type: str
    status: str
    error: str | None = None
    doc_type: str | None = None
    num_pages: int = 0
    created_at: datetime
    latest_analysis_id: uuid.UUID | None = None
    latest_analysis_status: str | None = None


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agent: str
    status: str
    input: dict
    output: dict
    tools: list
    error: str | None = None
    started_at: datetime
    duration_ms: int | None = None


class RiskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    finding_id: str
    clause_ref: str
    page: int
    category: str
    severity: str
    rationale: str
    recommendation: str
    explanation: str
    questions: list
    status: str


class ChatIn(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    document_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None
    include_legal: bool = True


class FeedbackIn(BaseModel):
    analysis_id: uuid.UUID | None = None
    target_id: str = ""
    rating: int = Field(ge=-1, le=1)
    comment: str = Field("", max_length=2000)


class LegalSourceIn(BaseModel):
    title: str
    source_type: str = "act"
    jurisdiction: str = "IN"
    version: str = ""
    effective_date: str = ""
    url: str = ""
    verified: bool = False
    sections: list[dict]  # [{"section": "s.27", "text": "..."}]
