"""Agent 工具配置测试。"""
from __future__ import annotations

from app.agent.tools import build_tools, rag_tool


def test_build_tools_includes_rag():
    tools = build_tools()
    names = [t.name for t in tools]
    assert "knowledge_base_search" in names


def test_rag_tool_is_described():
    assert "知识库" in rag_tool.description or "检索" in rag_tool.description


def test_load_mcp_tools_gracefully_fails_without_client():
    # 未传 client / 异常时返回空列表，实现优雅降级
    from app.agent.tools import _load_mcp_tools

    assert _load_mcp_tools(None) == []