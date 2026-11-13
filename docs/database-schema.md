# Database schema
See `backend/app/db/models/core.py` (19 tables from the brief). Document-derived rows cascade on delete.
Indexes: HNSW on both embedding columns, GIN full-text on chunk text. Use Alembic for production
(`alembic revision --autogenerate -m init && alembic upgrade head`); dev auto-creates tables.
