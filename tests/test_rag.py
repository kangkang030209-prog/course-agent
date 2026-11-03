"""retriever / ingest 的单元测试（不依赖 LLM，仅用字节分割与向量库）。"""
from __future__ import annotations

import pytest

from app.rag.ingest import split_documents
from app.rag.retriever import format_context, RetrievedChunk
from langchain_core.documents import Document


def test_split_documents_produces_chunks():
    doc = Document(page_content="题目一。\n\n" * 100, metadata={"source": "a.md"})
    chunks = split_documents([doc], chunk_size=50, chunk_overlap=5)
    assert len(chunks) > 1
    assert all("source" in c.metadata for c in chunks)


def test_format_context_contains_source():
    chunks = [
        RetrievedChunk(content="RAG 是检索增强生成。", source="rag.md", score=0.9),
        RetrievedChunk(content="Agent 使用 ReAct 范式。", source="agent.md", score=0.8),
    ]
    text = format_context(chunks)
    assert "rag.md" in text
    assert "agent.md" in text
    assert "RAG 是检索增强生成" in text


def test_format_context_truncates_long():
    chunks = [RetrievedChunk(content="x" * 5000, source="big.md", score=1.0)]
    text = format_context(chunks, max_chars=600)
    assert len(text) <= 640
    assert text.endswith("…")


def test_format_context_empty():
    assert format_context([]) == "（知识库为空，无检索结果）"


@pytest.mark.slow
def test_dummy_marker_to_keep_module():
    # 向量化检索的集成测试需要联网下载 embedding 模型，默认跳过，单独运行
    assert True