"""RAG 模块：知识库入库与检索。"""
from app.rag.ingest import ingest
from app.rag.retriever import (
    RetrievedChunk,
    format_context,
    retrieve,
)

__all__ = ["ingest", "retrieve", "format_context", "RetrievedChunk"]