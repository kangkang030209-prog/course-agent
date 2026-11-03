"""RAG 检索：从向量库按相似度取回相关文本块，并返回可引用的来源信息。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from app.config import settings


@dataclass
class RetrievedChunk:
    """一条检索结果，含来源引用。"""
    content: str
    source: str
    score: float


def get_vectorstore(
    embeddings: HuggingFaceEmbeddings | None = None,
) -> Chroma:
    from app.rag.ingest import build_vectorstore

    return build_vectorstore(
        embeddings or get_embeddings(), persist_dir=None, collection=None
    )


def get_embeddings() -> HuggingFaceEmbeddings:
    from app.rag.embeddings import get_embeddings as _get

    return _get()


def retrieve(
    query: str,
    top_k: int | None = None,
    embeddings: HuggingFaceEmbeddings | None = None,
) -> list[RetrievedChunk]:
    """对 query 进行向量检索，返回按相关度排序、可引用的结果。"""
    emb = embeddings or get_embeddings()
    store = get_vectorstore(emb)
    k = top_k or settings.retrieval_top_k
    docs = store.similarity_search_with_relevance_scores(query, k=k)
    results: list[RetrievedChunk] = []
    for doc, score in docs:
        src = doc.metadata.get("source", "未知来源")
        results.append(
            RetrievedChunk(content=doc.page_content, source=src, score=float(score))
        )
    return results


def format_context(chunks: Iterable[RetrievedChunk], max_chars: int = 3000) -> str:
    """把检索结果拼成给 LLM 的上下文（含来源），截断超长输出。"""
    parts: list[str] = []
    used = 0
    for c in chunks:
        block = f"[来源: {c.source}]\n{c.content}"
        if used + len(block) > max_chars:
            block = block[: max_chars - used] + "…"
        parts.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "\n\n---\n\n".join(parts) if parts else "（知识库为空，无检索结果）"