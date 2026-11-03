"""MCP 课程 server 的单元测试。"""
from __future__ import annotations

import pytest

from app.mcp_server.course_mcp import (
    get_course_schedule,
    get_homework,
    get_announcements,
    get_course_overview,
)


def test_get_course_schedule_has_entries():
    out = get_course_schedule()
    assert isinstance(out, str)
    assert "周一" in out or "课程" in out


def test_get_course_schedule_by_day():
    out = get_course_schedule("周一")
    assert "RAG" in out or "代码" in out or "课" in out


def test_get_homework_has_deadline():
    out = get_homework()
    assert "截止" in out.lower() or "deadline" in out.lower() or "11-" in out


def test_get_announcements_non_empty():
    out = get_announcements()
    assert isinstance(out, str) and out


def test_get_course_overview_contains_name():
    out = get_course_overview()
    assert "大模型应用开发" in out


@pytest.mark.skip(reason="print helper only")
def test_server_buildable():
    from app.mcp_server.course_mcp import build_server

    assert build_server() is not None