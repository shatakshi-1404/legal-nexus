"""Clause segmentation + clause-aware chunking. Pure Python (no heavy deps) so it is unit-testable."""
import re
from dataclasses import dataclass

# "1. Term", "Clause 3: Payment", "12) Notice". Sub-numbers like "1.1" or dates are NOT top-level.
TOP = re.compile(r"^\s*(?:(?:article|clause|section)\s+)?(\d{1,2})\s*[.):\-](?!\d)\s*(\S.*)?$", re.I)


@dataclass
class Segment:
    ref: str
    heading: str
    text: str
    page: int
    idx: int


@dataclass
class Chunk:
    clause_ref: str
    page: int
    text: str


def segment_clauses(pages: list[tuple[int, str]]) -> list[Segment]:
    """pages: [(page_number, text)] -> clause segments with first-line page attribution."""
    raw: list[dict] = []
    cur = {"heading": "Preamble", "lines": [], "page": pages[0][0] if pages else 1}
    for pno, text in pages:
        for line in text.splitlines():
            m = TOP.match(line)
            if m:
                raw.append(cur)
                head = (m.group(2) or f"Clause {m.group(1)}").strip()[:120]
                cur = {"heading": head, "lines": [line.strip()], "page": pno}
            elif line.strip():
                cur["lines"].append(line.strip())
    raw.append(cur)
    raw = [r for r in raw if len(" ".join(r["lines"])) >= 30]

    if len(raw) <= 1 and pages:  # unnumbered document: fall back to paragraph groups
        raw = []
        for pno, text in pages:
            buf, size = [], 0
            for para in re.split(r"\n\s*\n", text):
                para = para.strip()
                if not para:
                    continue
                buf.append(para)
                size += len(para)
                if size >= 900:
                    raw.append({"heading": buf[0][:80], "lines": buf, "page": pno})
                    buf, size = [], 0
            if buf:
                raw.append({"heading": buf[0][:80], "lines": buf, "page": pno})

    return [Segment(ref=f"CL-{i + 1:03d}", heading=r["heading"], text="\n".join(r["lines"]),
                    page=r["page"], idx=i) for i, r in enumerate(raw)]


def chunk_segments(segments: list[Segment], max_chars: int = 1500, overlap: int = 200) -> list[Chunk]:
    chunks: list[Chunk] = []
    for seg in segments:
        if len(seg.text) <= max_chars:
            chunks.append(Chunk(seg.ref, seg.page, seg.text))
            continue
        sentences = re.split(r"(?<=[.;])\s+", seg.text)
        buf = ""
        for s in sentences:
            if buf and len(buf) + len(s) + 1 > max_chars:
                chunks.append(Chunk(seg.ref, seg.page, buf.strip()))
                buf = buf[-overlap:] + " " + s
            else:
                buf = f"{buf} {s}".strip()
        if buf.strip():
            chunks.append(Chunk(seg.ref, seg.page, buf.strip()))
    return chunks
