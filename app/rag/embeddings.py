"""共享的 embedding 工厂。"""
from __future__ import annotations

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


def get_embeddings() -> HuggingFaceEmbeddings:
    """返回中文 embedding 封装（BAAI/bge-small-zh-v1.5，本地离线推理）。"""
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": settings.embedding_device},
        encode_kwargs={"normalize_embeddings": False},
    )