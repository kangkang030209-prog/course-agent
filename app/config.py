"""应用配置：从 .env 读取并集中管理。"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # LLM
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Embedding
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_device: str = "cpu"

    # 向量库
    chroma_db_dir: str = "./chroma_db"
    chroma_collection: str = "course_knowledge"

    # 数据
    course_data_dir: str = "./data"

    # MCP
    mcp_server_cmd: str = "python -m app.mcp_server.run"

    # 检索
    retrieval_top_k: int = 4
    chunk_size: int = 500
    chunk_overlap: int = 60

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def chroma_persist_dir(self) -> Path:
        p = Path(self.chroma_db_dir)
        return p if p.is_absolute() else PROJECT_ROOT / p

    @property
    def data_root(self) -> Path:
        p = Path(self.course_data_dir)
        return p if p.is_absolute() else PROJECT_ROOT / p


settings = Settings()