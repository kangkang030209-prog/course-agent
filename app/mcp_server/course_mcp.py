"""MCP 课程服务：把课程结构化信息（课程表/作业/公告）暴露为 MCP 工具。

通过标准 MCP 协议，agent（作为 MCP Client）可按需调用这些工具，
获得超出 RAG 文本检索能力之外的『事实性』课程数据。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.config import PROJECT_ROOT

DATA_FILE = "course_mcp_data.json"


def _load_data() -> dict[str, Any]:
    path = Path(PROJECT_ROOT) / "data" / DATA_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


# 创建 FastMCP 实例；name 用于日志/报错区分
mcp = FastMCP("course-mcp")


def _course_data() -> dict[str, Any]:
    return _load_data()


@mcp.tool()
def get_course_schedule(day: str = "") -> str:
    """查询课程表。day 为星期几（如「周一」/「Tuesday」，可空则返回完整课表）。"""
    data = _course_data()
    schedule = data.get("schedule", {})
    if not schedule:
        return "暂无课程表数据。"
    if day:
        key = day.lower()
        matched = {k: v for k, v in schedule.items() if key in k.lower() or day in k}
        if matched:
            return json.dumps(matched, ensure_ascii=False, indent=2)
        return f"未找到 {day} 的课程。可用：{list(schedule.keys())}"
    return json.dumps(schedule, ensure_ascii=False, indent=2)


@mcp.tool()
def get_homework(deadline_before: str = "") -> str:
    """查询作业及截止时间。deadline_before 为截止日期（YYYY-MM-DD，可空则返回全部）。"""
    data = _course_data()
    homework = data.get("homework", [])
    if not homework:
        return "暂无作业数据。"
    if deadline_before:
        filtered = [h for h in homework if str(h.get("deadline", "")) <= deadline_before]
        return json.dumps(filtered, ensure_ascii=False, indent=2)
    return json.dumps(homework, ensure_ascii=False, indent=2)


@mcp.tool()
def get_announcements() -> str:
    """查询最新的课程公告/重要通知。"""
    data = _course_data()
    anns = data.get("announcements", [])
    if not anns:
        return "暂无公告。"
    return json.dumps(anns, ensure_ascii=False, indent=2)


@mcp.tool()
def get_course_overview() -> str:
    """返回课程整体信息（课程名、大纲、考核方式、教师等）。"""
    data = _course_data()
    overview = {k: v for k, v in data.items() if k not in ("schedule", "homework", "announcements")}
    if not overview:
        return "暂无课程概览数据。"
    return json.dumps(overview, ensure_ascii=False, indent=2)


def build_server() -> FastMCP:
    return mcp


if __name__ == "__main__":
    mcp.run(transport="stdio")