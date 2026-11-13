"""LLM provider abstraction. Agents only call `structured()` / `complete()`; swap providers via env."""
import logging
from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


def get_chat_model(temperature: float = 0.0):
    s = get_settings()
    if s.llm_provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=s.groq_model, api_key=s.groq_api_key, temperature=temperature)
    from langchain_openai import ChatOpenAI  # any OpenAI-compatible endpoint
    return ChatOpenAI(model=s.openai_model, base_url=s.openai_base_url or None,
                      api_key=s.openai_api_key, temperature=temperature)


@lru_cache
def _langfuse_handler():
    s = get_settings()
    if not (s.langfuse_public_key and s.langfuse_secret_key):
        return None
    try:
        try:
            from langfuse.langchain import CallbackHandler  # langfuse v3
        except ImportError:
            from langfuse.callback import CallbackHandler  # langfuse v2
        return CallbackHandler(public_key=s.langfuse_public_key,
                               secret_key=s.langfuse_secret_key, host=s.langfuse_host)
    except Exception as e:  # observability must never break the pipeline
        log.warning("Langfuse disabled: %s", e)
        return None


def _cfg() -> dict:
    h = _langfuse_handler()
    return {"callbacks": [h]} if h else {}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
def structured(schema: type[T], system: str, user: str) -> T:
    model = get_chat_model().with_structured_output(schema)
    return model.invoke([("system", system), ("human", user)], config=_cfg())


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
def complete(system: str, user: str) -> str:
    return get_chat_model().invoke([("system", system), ("human", user)], config=_cfg()).content
