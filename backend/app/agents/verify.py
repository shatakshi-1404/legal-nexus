"""Deterministic citation verification: checks the ACTUAL source text, not LLM plausibility."""


def norm(s: str) -> str:
    return " ".join(s.lower().split())


def excerpt_in_source(excerpt: str | None, source_text: str, min_len: int = 20) -> bool:
    if not excerpt:
        return False
    e = norm(excerpt)
    return len(e) >= min_len and e in norm(source_text)


def label_map(hits: list[dict]) -> dict[str, dict]:
    """Stable short labels L1..Ln for a clause's evidence list (shared by agents and critic)."""
    return {f"L{i + 1}": h for i, h in enumerate(hits)}


def verify_item(item: dict, evidence_hits: list[dict]) -> tuple[str, dict]:
    """Return (status, citation_fields). status: verified | flagged | rejected."""
    label, excerpt = item.get("evidence_label"), item.get("legal_excerpt")
    if not label:
        return "flagged", {}  # document-only observation, no legal source cited
    hit = label_map(evidence_hits).get(label)
    if hit is None:
        return "rejected", {}  # cites evidence that was never retrieved
    fields = {"legal_source_id": hit["meta"].get("source_id", ""),
              "legal_section": hit["meta"].get("section", "")}
    if excerpt and excerpt_in_source(excerpt, hit["text"]):
        return "verified", {**fields, "legal_excerpt": excerpt}
    if excerpt:
        return "rejected", fields  # fabricated / altered quotation
    return "flagged", fields
