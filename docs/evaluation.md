# Evaluation plan
1. Build a labelled legal retrieval set (>=100 queries) and a clause-risk set annotated by a lawyer.
2. Run `evaluation/rag/run_eval.py` for dense / hybrid / hybrid+rerank; add RAGAS/DeepEval for faithfulness.
3. Add agent metrics from `agent_runs` and `findings.status` (unsupported rate, retries, human interventions).
4. Record latency, tokens, cost per analysis (Langfuse). Report only measured numbers.
