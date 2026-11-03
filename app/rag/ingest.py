"""知识库文档加载与入库。

- 扫描 COURSE_DATA_DIR 下 .md / .txt / .markdown 文件
- 使用递归字符切分器分块
- 写入本地 Chroma 向量库（持久化）
"""
from __future__ import annotations

import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)

_SUPPORTED_SUFFIX = {".md", ".markdown", ".txt"}


def discover_documents(data_dir: Path) -> list[Document]:
    """加载 data_dir 下所有受支持文本文件为 Document，带上来源元数据。"""
    docs: list[Document] = []
    if not data_dir.exists():
        logger.warning("数据目录不存在: %s", data_dir)
        return docs
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _SUPPORTED_SUFFIX:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            logger.warning("读取失败，跳过: %s", path)
            continue
        docs.append(
            Document(
                page_content=content,
                metadata={"source": path.name, "path": str(path)},
            )
        )
    logger.info("扫描到 %d 个文档文件", len(docs))
    return docs


def split_documents(
    docs: list[Document], chunk_size: int | None = None, chunk_overlap: int | None = None
) -> list[Document]:
    """切分文档为固定大小文本块。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap or settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""],
        length_function=len,
    )
    return splitter.split_documents(docs)


def build_vectorstore(
    embeddings: HuggingFaceEmbeddings,
    persist_dir: Path | None = None,
    collection: str | None = None,
) -> Chroma:
    """创建或复用持久化的 Chroma 向量库连接。"""
    dir_path = persist_dir or settings.chroma_persist_dir
    dir_path.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=collection or settings.chroma_collection,
        embedding_function=embeddings,
        persist_directory=str(dir_path),
    )


def ingest(
    embeddings: HuggingFaceEmbeddings | None = None,
    data_dir: Path | None = None,
    force_rebuild: bool = False,
) -> int:
    """执行入库：加载 -> 切分 -> 写入向量库。返回写入的块数。"""
    import chromadb  # 延迟导入，降低启动开销

    data_root = data_dir or settings.data_root
    emb = embeddings
    if emb is None:
        emb = get_embeddings_for_ingest()
    docs = discover_documents(data_root)
    if not docs:
        logger.warning("没有发现任何可导入的课程资料，已跳过入库。")
        return 0
    chunks = split_documents(docs)
    if force_rebuild:
        # 重建集合，避免旧数据残留
        client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_dir)
        )
        client.delete_collection(settings.chroma_collection)
        logger.info("已清空旧向量库集合 %s", settings.chroma_collection)
    store = build_vectorstore(emb)
    store.add_documents(chunks)
    logger.info(
        "入库完成：文件 %d 个，文本块 %d 个，写入集合 %s",
        len(docs),
        len(chunks),
        settings.chroma_collection,
    )
    return len(chunks)


def get_embeddings_for_ingest():
    from app.rag.embeddings import get_embeddings

    return get_embeddings()