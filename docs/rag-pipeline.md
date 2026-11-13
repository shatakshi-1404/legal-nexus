# RAG pipeline
Ingestion: validate -> PyMuPDF/python-docx -> Tesseract OCR for text-less pages -> clause segmentation
(numbered headings, paragraph fallback) -> clause-aware chunks (<=1500 chars, 200 overlap) -> bge-small embeddings -> pgvector (HNSW cosine).
Retrieval: dense + Postgres FTS (OR-ed terms, ts_rank_cd) -> RRF (k=60) -> cross-encoder rerank -> evidence selection.
Agentic: legal_rag judges sufficiency via `MIN_RERANK_SCORE`, rewrites weak queries, retries up to 2 times.
Citations: `agents/verify.py` (verified / flagged / rejected).
