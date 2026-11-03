"""Agent 编排：基于 LangGraph 的 ReAct Agent，集成 RAG 与 MCP 工具。

流程：
- 异步 MCP Client 管理（stdio 连接 course-mcp server）
- 把 RAG 工具 + MCP 工具一起挂载给 ReAct agent
- 处理 MCP 不可用时的降级（仅保留 RAG 工具）
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.prebuilt import create_react_agent

from app.config import settings
from app.agent.tools import build_tools

logger = logging.getLogger(__name__)


def _system_prompt() -> str:
    return (
        "你是「课程智能助手」，帮助同学解答《大模型应用开发实战》课程相关问题。\n"
        "你可以使用两类工具：\n"
        "1. knowledge_base_search：检索课程知识库（大纲、讲义、考核方式等文本资料）。"
        "2. MCP 课程工具（get_course_schedule / get_homework / get_announcements / get_course_overview）："
        "查询结构化事实，如课程表、作业截止、公告。\n"
        "规则：\n"
        "- 知识/概念类问题优先查知识库；课程表、作业、公告等事实性问题优先用 MCP 工具。\n"
        "- 回答需简洁、准确；若引用了知识库内容，尽量注明来源。\n"
        "- 若工具不可用导致无法获取准确信息，明确告知用户当前缺少该能力。"
    )


def _create_llm() -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    if not settings.deepseek_api_key:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY，请在 .env 中设置后重试。")
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.3,
    )


class CourseAssistant:
    """课程智能助手：管理模型、工具与 MCP 生命周期（异步 MCP 客户端）。"""

    def __init__(self, llm: BaseChatModel | None = None, use_mcp: bool = True) -> None:
        self.llm = llm or _create_llm()
        self.use_mcp = use_mcp
        self.mcp_tools: list[Any] = []
        self.mcp_client: Any = None
        self.agent = None
        self.ready = False

    # ---- MCP 生命周期（异步） ----
    async def _start_mcp(self) -> bool:
        """异步启动 MCP 客户端并加载工具。成功返回 True。"""
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient

            # MCP server 必须用当前 venv 的解释器启动，否则找不到已安装的包。
            # settings.mcp_server_cmd 形如 "python -m app.mcp_server.run"，
            # 这里用 sys.executable 替换 command，保留其余参数。
            import sys

            cmd_parts = settings.mcp_server_cmd.split()
            command = sys.executable  # 当前 venv 的 Python
            args = cmd_parts[1:] or ["-m", "app.mcp_server.run"]

            client = MultiServerMCPClient(
                {
                    "course": {
                        "command": command,
                        "args": args,
                        "transport": "stdio",
                    }
                }
            )
            tools = await client.get_tools()
            if tools:
                self.mcp_client = client
                self.mcp_tools = tools
                logger.info("MCP 客户端已启动，加载工具: %s", [t.name for t in tools])
                return True
            # 无工具时也保留引用（无显式 close），避免卸载失败
            self.mcp_client = client
            return False
        except Exception as exc:  # noqa: BLE001
            logger.warning("MCP 启动失败（将降级为纯 RAG）: %s", exc)
            return False

    async def _stop_mcp(self) -> None:
        # langchain-mcp-adapters 0.3.x 的 MultiServerMCPClient 每个工具调用
        # 都会新建独立 session，客户端本身无显式关闭方法，无需额外清理。
        self.mcp_client = None

    async def build(self) -> "CourseAssistant":
        """异步构建 agent（需要启动 MCP，故为异步）。"""
        base_tools = build_tools()  # 至少包含 RAG 工具
        all_tools: list[Any] = list(base_tools)
        if self.use_mcp and await self._start_mcp():
            all_tools.extend(self.mcp_tools)
        else:
            logger.info("当前仅使用 RAG 工具运行（MCP 不可用）。")
        react = create_react_agent(self.llm, all_tools, prompt=_system_prompt())
        self.agent = react
        self.ready = True
        return self

    # ---- 对外接口（可同步/异步复用） ----
    async def aask(self, question: str) -> str:
        """异步执行一次会话问询，返回回答文本。"""
        if not self.ready or self.agent is None:
            raise RuntimeError("Agent 未初始化，请先调用 await build()。")
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        return self._extract_answer(result)

    def ask(self, question: str) -> str:
        """同步便捷封装（内部跑一次事件循环）。"""
        return asyncio.run(self.aask(question))

    async def astream(self, question: str):
        """异步生成式返回回答片段。"""
        if not self.ready or self.agent is None:
            raise RuntimeError("Agent 未初始化，请先调用 await build()。")
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        yield self._extract_answer(result)

    @staticmethod
    def _extract_answer(result: dict[str, Any]) -> str:
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if getattr(msg, "type", "") == "ai" and msg.content:
                return msg.content if isinstance(msg.content, str) else str(msg.content)
        return "（没有生成回答）"

    async def aclose(self) -> None:
        await self._stop_mcp()


# 便捷函数：默认配置创建，需 await build()
def create_assistant() -> CourseAssistant:
    return CourseAssistant()