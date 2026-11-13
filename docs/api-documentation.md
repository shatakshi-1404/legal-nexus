# API
Interactive docs at `/docs` when the backend runs. Note: `POST /analysis/{id}/start` takes a DOCUMENT id;
all other `/analysis/{id}/...` routes take an ANALYSIS id. Extras beyond the brief: `/analysis/{id}/approve`,
`/analysis/{id}/resume`, `/knowledge/ingest` (admin), `/reports/{id}?format=md`.
SSE: `/analysis/{id}/stream?token=<jwt>`.
