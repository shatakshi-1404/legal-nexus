from typing import Literal

from pydantic import BaseModel, Field

CLAUSE_TYPES = ["parties", "term", "payment", "termination", "confidentiality", "non_compete",
                "indemnity", "liability_limitation", "governing_law", "dispute_resolution",
                "ip_ownership", "data_protection", "renewal", "security_deposit", "maintenance",
                "scope_of_services", "warranty", "penalty", "assignment", "definitions",
                "signature", "boilerplate", "other"]
DOC_TYPES = ["rental_agreement", "employment_agreement", "nda", "service_agreement",
             "vendor_agreement", "privacy_policy", "other"]
RISK_CATEGORIES = ["unfair_termination", "unlimited_liability", "one_sided_indemnity", "excessive_penalty",
                   "restraint_of_trade", "unfavourable_jurisdiction", "data_privacy", "auto_renewal",
                   "ambiguous_terms", "ip_assignment", "payment_terms", "other"]


class DocInfo(BaseModel):
    doc_type: Literal[tuple(DOC_TYPES)]  # type: ignore[valid-type]
    parties: list[str] = []
    effective_date: str | None = None
    governing_law: str | None = None
    summary: str = ""


class ClauseLabel(BaseModel):
    clause_ref: str
    clause_type: Literal[tuple(CLAUSE_TYPES)]  # type: ignore[valid-type]


class ClauseLabels(BaseModel):
    labels: list[ClauseLabel]


class RiskItem(BaseModel):
    clause_ref: str
    category: Literal[tuple(RISK_CATEGORIES)]  # type: ignore[valid-type]
    severity: Literal["low", "medium", "high"]
    rationale: str
    recommendation: str = ""
    evidence_label: str | None = Field(None, description="e.g. L1; must be a supplied label")
    legal_excerpt: str | None = Field(None, description="verbatim text from the cited evidence")


class RiskResult(BaseModel):
    items: list[RiskItem] = []


class ComplianceItem(BaseModel):
    clause_ref: str
    status: Literal["compliant", "potential_issue", "insufficient_evidence"]
    rationale: str
    evidence_label: str | None = None
    legal_excerpt: str | None = None


class ComplianceResult(BaseModel):
    items: list[ComplianceItem] = []


class Explanation(BaseModel):
    clause_ref: str
    plain_language: str
    questions: list[str] = []


class ExplanationResult(BaseModel):
    items: list[Explanation] = []


class Queries(BaseModel):
    queries: list[str]


class Rewritten(BaseModel):
    query: str


class ChatAnswer(BaseModel):
    answer: str
    cited: list[str] = []
    sufficient: bool = True
