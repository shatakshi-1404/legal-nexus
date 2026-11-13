"""Benchmark retrieval modes (dense vs hybrid vs hybrid+rerank) on a labelled dataset.
Run from repo root with the backend env + a populated legal KB:
    python -m evaluation.rag.run_eval evaluation/datasets/legal_retrieval_sample.jsonl
The sample dataset has 5 queries: use it to test the harness, NOT to report results.
Build a larger, independently labelled dataset before quoting any numbers."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.db.session import SessionLocal  # noqa: E402
from app.retrieval.hybrid import MODES, HybridRetriever  # noqa: E402

K = 5


def main(path: str):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    report = {}
    with SessionLocal() as db:
        r = HybridRetriever(db)
        for mode in MODES:
            rec, prec, t0 = [], [], time.time()
            for row in rows:
                hits = r.search(row["query"], kind="legal", mode=mode, top_k=K)
                got = {h.meta.get("section") for h in hits}
                rel = set(row["relevant"])
                rec.append(len(got & rel) / len(rel))
                prec.append(len([h for h in hits if h.meta.get("section") in rel]) / K)
            report[mode] = {f"recall@{K}": round(sum(rec) / len(rec), 3), f"precision@{K}": round(sum(prec) / len(prec), 3),
                            "avg_latency_s": round((time.time() - t0) / len(rows), 3), "n_queries": len(rows)}
    out = Path(__file__).resolve().parents[1] / "reports" / "retrieval_benchmark.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
