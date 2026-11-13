from functools import lru_cache

from app.core.config import get_settings

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "  # bge convention


@lru_cache
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(get_settings().embedding_model)


def embed_documents(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return _model().encode(texts, batch_size=32, normalize_embeddings=True).tolist()


def embed_query(query: str) -> list[float]:
    return _model().encode(QUERY_PREFIX + query, normalize_embeddings=True).tolist()
