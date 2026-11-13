import uuid

from sqlalchemy.orm import Session

from app.core import llm
from app.db.models import Conversation, Message, User
from app.prompts import templates as P
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.query_tools import decompose
from app.schemas.agents import ChatAnswer


def answer(db: Session, user: User, question: str, document_id: uuid.UUID | None,
           include_legal: bool, conversation_id: uuid.UUID | None) -> dict:
    conv = db.get(Conversation, conversation_id) if conversation_id else None
    if conv is None or conv.user_id != user.id:
        conv = Conversation(user_id=user.id, document_id=document_id)
        db.add(conv)
        db.commit()
    retriever = HybridRetriever(db)
    seen, sources = set(), []
    for q in decompose(question):
        batches = []
        if document_id:
            batches.append(("document", retriever.search(q, kind="document", owner_id=user.id,
                                                         document_id=document_id, top_k=4)))
        if include_legal:
            batches.append(("legal", retriever.search(q, kind="legal", top_k=3)))
        for kind, hits in batches:
            for h in hits:
                if h.id not in seen:
                    seen.add(h.id)
                    sources.append({"label": f"S{len(sources) + 1}", "kind": kind, "text": h.text, "meta": h.meta})
    ctx = "\n\n".join(f"[{s['label']}] ({s['kind']}) {s['text'][:900]}" for s in sources) or "(no sources)"
    res = llm.structured(ChatAnswer, P.CHAT, f"QUESTION: {question}\n\nSOURCES:\n{ctx}")
    labels = {s["label"] for s in sources}
    verified = all(c in labels for c in res.cited) and (bool(res.cited) or not res.sufficient)
    text = res.answer if res.sufficient else f"I can't answer this reliably from the available sources. {res.answer}"
    cited_sources = [s for s in sources if s["label"] in res.cited]
    db.add(Message(conversation_id=conv.id, role="user", content=question))
    db.add(Message(conversation_id=conv.id, role="assistant", content=text, sources=cited_sources))
    db.commit()
    return {"conversation_id": str(conv.id), "answer": text, "sources": cited_sources,
            "citations_verified": verified, "sufficient": res.sufficient}
