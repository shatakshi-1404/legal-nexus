"""The agents. Deterministic Python where possible; LLM only where language understanding is needed."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.agents.base import State, tracked
from app.agents.verify import label_map, verify_item
from app.core import llm
from app.core.config import get_settings
from app.db.models import (Analysis, Citation, Clause, ComplianceFinding, Document, DocumentPage,
                           Risk)
from app.db.session import SessionLocal
from app.prompts import templates as P
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.query_tools import rewrite_query
from app.schemas.agents import (ClauseLabels, ComplianceResult, DocInfo, ExplanationResult,
                                RiskResult)
from app.services.report import build_report

SKIP_TYPES = {"definitions", "signature", "boilerplate"}
MAX_RETRIEVAL_ATTEMPTS = 2


def _substantive(clauses: list[dict]) -> list[dict]:
    return [c for c in clauses if c["type"] not in SKIP_TYPES and len(c["text"]) >= 80]


def _batches(items: list, n: int):
    for i in range(0, len(items), n):
        yield items[i:i + n]


def _evidence_block(ev: list[dict]) -> str:
    if not ev:
        return "  (no legal evidence found)"
    return "\n".join(f"  [{lab}] ({h['meta'].get('source_title', '')} {h['meta'].get('section', '')}) {h['text'][:700]}"
                     for lab, h in label_map(ev).items())


# 1. Supervisor (deterministic orchestrator: plans + routing functions live in workflows/graph.py)
@tracked("supervisor")
def supervisor_plan(state: State) -> dict:
    return {"plan": ["document", "clause", "legal_rag", "risk||compliance", "explain", "critic", "finalize"],
            "retrieval_attempts": 0, "critic_loops": 0, "weak_refs": [], "loop_refs": []}


# 2. Document Understanding Agent
@tracked("document_agent", tools=["llm.structured"])
def document_node(state: State) -> dict:
    did = uuid.UUID(state["document_id"])
    with SessionLocal() as s:
        pages = s.scalars(select(DocumentPage).where(DocumentPage.document_id == did)
                          .order_by(DocumentPage.page_number)).all()
        text = "\n".join(p.text for p in pages)[:6000]
        info = llm.structured(DocInfo, P.DOC_UNDERSTANDING, text)
        doc = s.get(Document, did)
        doc.doc_type, doc.doc_meta = info.doc_type, info.model_dump()
        s.commit()
    return {"doc_info": info.model_dump()}


# 3. Clause Extraction Agent (segmentation done at ingestion; LLM classifies)
@tracked("clause_agent", tools=["llm.structured", "db.clauses"])
def clause_node(state: State) -> dict:
    did = uuid.UUID(state["document_id"])
    cap = get_settings().max_clauses_per_analysis
    with SessionLocal() as s:
        rows = s.scalars(select(Clause).where(Clause.document_id == did)
                         .order_by(Clause.order_idx).limit(cap)).all()
        for batch in _batches(rows, 20):
            prompt = "\n\n".join(f"{c.clause_ref}: {c.heading}\n{c.text[:500]}" for c in batch)
            labels = {l.clause_ref: l.clause_type for l in llm.structured(ClauseLabels, P.CLAUSE_LABELING, prompt).labels}
            for c in batch:
                c.clause_type = labels.get(c.clause_ref, "other")
        s.commit()
        clauses = [{"id": str(c.id), "ref": c.clause_ref, "heading": c.heading, "text": c.text,
                    "page": c.page, "type": c.clause_type or "other"} for c in rows]
    return {"clauses": clauses}


# 4. Legal RAG Agent (agentic: judges sufficiency, rewrites queries, retries)
@tracked("legal_rag_agent", tools=["pgvector", "postgres_fts", "rrf", "cross_encoder", "llm.rewrite"])
def legal_rag_node(state: State) -> dict:
    s_ = get_settings()
    attempts = state.get("retrieval_attempts", 0)
    clauses = {c["ref"]: c for c in _substantive(state["clauses"])}
    targets = [r for r in (state.get("weak_refs") or list(clauses)) if r in clauses]
    evidence, weak = dict(state.get("evidence", {})), []
    with SessionLocal() as db:
        retriever = HybridRetriever(db)
        for i, ref in enumerate(targets):
            c = clauses[ref]
            q = f"{c['type'].replace('_', ' ')} {c['heading']} {c['text'][:300]}"
            if attempts > 0 and i < 10:  # retry path: rewrite the query (capped)
                q = rewrite_query(q)
            hits = retriever.search(q, kind="legal", top_k=4, mode="hybrid_rerank")
            evidence[ref] = [h.asdict() for h in hits]
            if not hits or hits[0].score < s_.min_rerank_score:
                weak.append(ref)
    return {"evidence": evidence, "weak_refs": weak, "retrieval_attempts": attempts + 1}


def _clause_prompt(c: dict, evidence: dict) -> str:
    return f"### {c['ref']} [{c['type']}] {c['heading']}\nCLAUSE: {c['text'][:900]}\nEVIDENCE:\n{_evidence_block(evidence.get(c['ref'], []))}"


# 5. Risk Detection Agent
@tracked("risk_agent", tools=["llm.structured"])
def risk_node(state: State) -> dict:
    items = []
    for batch in _batches(_substantive(state["clauses"]), 6):
        res = llm.structured(RiskResult, P.RISK, "\n\n".join(_clause_prompt(c, state.get("evidence", {})) for c in batch))
        items += [i.model_dump() for i in res.items]
    return {"risks": items}


# 6. Compliance Analysis Agent
@tracked("compliance_agent", tools=["llm.structured"])
def compliance_node(state: State) -> dict:
    items = []
    ev = state.get("evidence", {})
    for batch in _batches([c for c in _substantive(state["clauses"]) if ev.get(c["ref"])], 6):
        res = llm.structured(ComplianceResult, P.COMPLIANCE, "\n\n".join(_clause_prompt(c, ev) for c in batch))
        items += [i.model_dump() for i in res.items]
    return {"compliance": items}


# 7. Explanation Agent
@tracked("explanation_agent", tools=["llm.structured"])
def explain_node(state: State) -> dict:
    refs = {r["clause_ref"] for r in state.get("risks", [])} | \
           {c["clause_ref"] for c in state.get("compliance", []) if c["status"] == "potential_issue"}
    by_ref = {c["ref"]: c for c in state["clauses"]}
    notes = {}
    for batch in _batches(sorted(refs & by_ref.keys()), 8):
        prompt = "\n\n".join(f"{r}: {by_ref[r]['text'][:600]}\nFINDINGS: " + "; ".join(
            x["rationale"] for x in state.get("risks", []) + state.get("compliance", []) if x["clause_ref"] == r)
            for r in batch)
        for e in llm.structured(ExplanationResult, P.EXPLAIN, prompt).items:
            notes[e.clause_ref] = {"plain_language": e.plain_language, "questions": e.questions}
    return {"explanations": notes}


# 8a. Critic: deterministic evidence verification (rejects/flags unsupported findings)
@tracked("critic_agent", tools=["citation_verifier"])
def critic_node(state: State) -> dict:
    by_ref = {c["ref"]: c for c in state["clauses"]}
    ev = state.get("evidence", {})
    findings, n = [], 0

    def add(kind, item, extra):
        nonlocal n
        clause = by_ref.get(item["clause_ref"])
        if clause is None:
            status, cit = "rejected", {}
        else:
            status, cit = verify_item(item, ev.get(item["clause_ref"], []))
        n += 1
        f = {"finding_id": f"F-{n:03d}", "kind": kind, "clause_ref": item["clause_ref"],
             "rationale": item["rationale"], "status": status,
             "document_page": clause["page"] if clause else 0,
             "document_excerpt": clause["text"][:400] if clause else "",
             "legal_source_id": cit.get("legal_source_id", ""), "legal_section": cit.get("legal_section", ""),
             "legal_excerpt": cit.get("legal_excerpt", ""), "citation_verified": status == "verified",
             "explanation": state.get("explanations", {}).get(item["clause_ref"], {}).get("plain_language", ""),
             "questions": state.get("explanations", {}).get(item["clause_ref"], {}).get("questions", []), **extra}
        findings.append(f)

    for r in state.get("risks", []):
        add("risk", r, {"category": r["category"], "severity": r["severity"], "recommendation": r["recommendation"]})
    compliant = 0
    for c in state.get("compliance", []):
        if c["status"] == "compliant":
            compliant += 1
            continue
        add("compliance", c, {"compliance_status": c["status"]})
        f = findings[-1]
        if f["status"] != "verified" and f["compliance_status"] == "potential_issue":
            f["compliance_status"] = "insufficient_evidence"  # an issue without verified evidence is not asserted
            f["status"] = "flagged" if f["status"] != "rejected" else "rejected"

    rejected = [f for f in findings if f["status"] == "rejected"]
    loops = state.get("critic_loops", 0)
    ratio = len(rejected) / len(findings) if findings else 0
    loop_refs = sorted({f["clause_ref"] for f in rejected}) if ratio > 0.4 and loops < 1 else []
    stats = {"total": len(findings), "verified": sum(f["status"] == "verified" for f in findings),
             "flagged": sum(f["status"] == "flagged" for f in findings), "rejected": len(rejected),
             "compliant_clauses": compliant, "unsupported_rate": round(ratio, 3)}
    return {"findings": findings, "stats": stats, "loop_refs": loop_refs,
            "weak_refs": loop_refs, "critic_loops": loops + (1 if loop_refs else 0)}


# 8b. Report: persists findings + builds the report (runs after optional human approval)
@tracked("report_agent", tools=["postgres"])
def finalize_node(state: State) -> dict:
    aid, did = uuid.UUID(state["analysis_id"]), uuid.UUID(state["document_id"])
    report = build_report(state.get("doc_info", {}), state.get("findings", []), state.get("stats", {}))
    with SessionLocal() as s:
        for f in state.get("findings", []):
            if f["kind"] == "risk":
                s.add(Risk(analysis_id=aid, finding_id=f["finding_id"], clause_ref=f["clause_ref"],
                           page=f["document_page"], category=f["category"], severity=f["severity"],
                           rationale=f["rationale"], recommendation=f["recommendation"],
                           explanation=f["explanation"], questions=f["questions"], status=f["status"]))
            else:
                s.add(ComplianceFinding(analysis_id=aid, finding_id=f["finding_id"], clause_ref=f["clause_ref"],
                                        compliance_status=f["compliance_status"], rationale=f["rationale"],
                                        explanation=f["explanation"], status=f["status"]))
            if f["status"] != "rejected":
                s.add(Citation(analysis_id=aid, finding_id=f["finding_id"], document_id=did,
                               clause_ref=f["clause_ref"], document_page=f["document_page"],
                               document_excerpt=f["document_excerpt"], legal_source_id=f["legal_source_id"],
                               legal_section=f["legal_section"], legal_excerpt=f["legal_excerpt"],
                               citation_verified=f["citation_verified"]))
        a = s.get(Analysis, aid)
        a.status, a.report, a.completed_at = "completed", report, datetime.now(timezone.utc)
        s.commit()
    return {"report": report}
