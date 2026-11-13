# Evaluation

Implemented: `rag/run_eval.py` (Recall@5, Precision@5, latency across dense / hybrid / hybrid+rerank).

Not yet implemented (planned, see docs/evaluation.md): RAGAS / DeepEval faithfulness and answer relevancy,
agent-level metrics (task completion, routing accuracy, unsupported-finding rate), cost and token tracking,
and the fourth benchmark system (agentic RAG + multi-agent verification).
The targets in the project brief (Recall@5 >= 85% etc.) are goals to investigate, not results.
