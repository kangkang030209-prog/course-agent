"""Agent 工具集。

包含两类工具：
- RAG 检索工具（本地知识库语义搜索）
- MCP 课程工具（通过 MCP 客户端从 course-mcp server 动态挂载）
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool

from app.config import settings
from app.rag.retriever import format_context, retrieve

logger = logging.getLogger(__name__)


def _rag_search(query: str) -> str:
    """在课程知识库中检索，返回相关内容的文本（含来源），供回答参考。"""
    try:
        chunks = retrieve(query)
    except Exception as exc:  # noqa: BLE001
        logger.warning("RAG 检索失败: %s", exc)
        return "（知识库检索失败，请基于已有知识回答）"
    return format_context(chunks)


rag_tool = StructuredTool.from_function(
    func=_rag_search,
    name="knowledge_base_search",
    description=(
        "在课程知识库中进行语义检索。当问题涉及课程大纲、某讲内容、RAG/Agent/MCP 概念、"
        "考核方式等知识型内容时调用。输入为用户的问题或检索关键字（中文）。"
        "返回多条相关的知识点文本片段（含来源），可直接作为回答依据。"
    ),
)


def _load_mcp_tools(mcp_client: Any) -> list[BaseTool]:
    """从给定的 MCP 客户端加载工具。mc 为 langchain-mcp-adapters 客户端。"""
    if mcp_client is None:
        return []
    try:
        from langchain_mcp_adapters.tools import load_mcp_tools

        tools = load_mcp_tools(mcp_client)
        logger.info("已从 MCP 加载 %d 个工具", len(tools))
        return tools
    except Exception as exc:  # noqa: BLE001
        logger.warning("加载 MCP 工具失败: %s", exc)
        return []


def build_tools() -> list[BaseTool]:
    """构建 agent 的完整工具列表：RAG 工具 + 可用的 MCP 工具。"""
    return [rag_tool]