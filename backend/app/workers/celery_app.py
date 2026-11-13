from celery import Celery

from app.core.config import get_settings

s = get_settings()
celery = Celery("legalnexus", broker=s.redis_url, backend=s.redis_url)
celery.conf.task_always_eager = s.celery_eager
celery.conf.task_acks_late = True


@celery.task(name="ingest_document", autoretry_for=(Exception,), max_retries=1)
def ingest_document_task(doc_id: str):
    from app.services.documents import ingest_document
    ingest_document(doc_id)


@celery.task(name="run_analysis")
def run_analysis_task(analysis_id: str, resume: bool = False):
    from app.services.analysis import run_analysis
    run_analysis(analysis_id, resume)
