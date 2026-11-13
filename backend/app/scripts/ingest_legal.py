"""Load legal reference sources: python -m app.scripts.ingest_legal ../knowledge_base/sources/*.json"""
import json
import sys

from app.db.base import Base
from app.db.session import SessionLocal, engine
import app.db.models  # noqa: F401
from app.services.knowledge import ingest_legal_source

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for path in sys.argv[1:]:
            for src in json.load(open(path, encoding="utf-8")):
                s = ingest_legal_source(db, {k: v for k, v in src.items() if k != "sections"}, src["sections"])
                print(f"ingested {s.title}: {len(src['sections'])} sections")
