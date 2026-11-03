"""FastAPI 后端：健康检查 / 入库 / 对话接口。"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent.service import CourseAssistant
from app.rag.ingest import ingest

logger = logging.getLogger(__name__)

_assistant: CourseAssistant | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期：启动时初始化助手，关闭时释放。"""
    global _assistant
    _assistant = CourseAssistant()
    try:
        await _assistant.build()
    except Exception:  # noqa: BLE001
        logger.exception("初始化助手失败，MCP 与对话可能不可用")
    yield
    if _assistant is not None:
        await _assistant.aclose()
        _assistant = None


app = FastAPI(
    title="课程智能助手",
    description="AI Agent + MCP + RAG 课程智能助手后端",
    version="0.1.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="用户提问")


class ChatResponse(BaseModel):
    answer: str
    mcp_used: bool = False


class IngestResponse(BaseModel):
    ingested: int


def get_assistant() -> CourseAssistant:
    if _assistant is None:
        raise RuntimeError("助手尚未初始化")
    return _assistant


@app.get("/health")
def health() -> dict:
    try:
        mcp_ok = bool(_assistant and _assistant.mcp_tools)
        ready = bool(_assistant and _assistant.ready)
    except Exception:  # noqa: BLE001
        mcp_ok, ready = False, False
    return {"status": "ok", "ready": ready, "mcp_available": mcp_ok}


@app.get("/")
def root() -> dict:
    return {"message": "课程智能助手运行中", "docs": "/docs"}


@app.post("/ingest", response_model=IngestResponse)
def ingest_endpoint(force_rebuild: bool = False) -> IngestResponse:
    try:
        count = ingest(force_rebuild=force_rebuild)
    except Exception as exc:  # noqa: BLE001
        logger.exception("入库失败")
        raise HTTPException(status_code=500, detail=f"入库失败: {exc}") from exc
    return IngestResponse(ingested=count)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        assistant = get_assistant()
    except Exception as exc:  # noqa: BLE001
        logger.exception("初始化助手失败")
        raise HTTPException(status_code=500, detail=f"初始化失败: {exc}") from exc
    try:
        answer = await assistant.aask(req.question)
    except Exception as exc:  # noqa: BLE001
        logger.exception("对话失败")
        raise HTTPException(status_code=500, detail=f"对话失败: {exc}") from exc
    return ChatResponse(answer=answer, mcp_used=bool(assistant.mcp_tools))


def main() -> None:
    import uvicorn

    uvicorn.run("app.api.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()