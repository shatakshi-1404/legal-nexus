from app.prompts.templates import DISCLAIMER

SEV_ORDER = {"high": 0, "medium": 1, "low": 2}


def build_report(doc_info: dict, findings: list[dict], stats: dict) -> dict:
    shown = [f for f in findings if f["status"] != "rejected"]
    shown.sort(key=lambda f: (SEV_ORDER.get(f.get("severity", "low"), 3), f["finding_id"]))
    by_sev = {s: sum(1 for f in shown if f.get("severity") == s) for s in ("high", "medium", "low")}
    return {"summary": doc_info.get("summary", ""), "doc_info": doc_info, "severity_counts": by_sev,
            "stats": stats, "findings": shown, "disclaimer": DISCLAIMER}


def report_markdown(report: dict) -> str:
    di = report.get("doc_info", {})
    out = [f"# Legal Intelligence Report", f"**Type:** {di.get('doc_type', '-')}  ",
           f"**Parties:** {', '.join(di.get('parties', [])) or '-'}  ",
           f"**Governing law:** {di.get('governing_law') or '-'}", "", report.get("summary", ""), "",
           f"Severity: {report.get('severity_counts')}", "", "## Findings"]
    for f in report.get("findings", []):
        out += [f"### {f['finding_id']} - {f['clause_ref']} (p.{f['document_page']}) "
                f"[{f.get('severity') or f.get('compliance_status')}] - {f['status']}",
                f["rationale"], f"> Clause: {f['document_excerpt'][:300]}"]
        if f.get("legal_excerpt"):
            out.append(f"> Source ({f['legal_section']}): {f['legal_excerpt']}  (verified: {f['citation_verified']})")
        if f.get("explanation"):
            out.append(f"**In plain language:** {f['explanation']}")
        for q in f.get("questions", []):
            out.append(f"- Ask: {q}")
        out.append("")
    out.append(f"---\n{report.get('disclaimer', '')}")
    return "\n".join(out)
