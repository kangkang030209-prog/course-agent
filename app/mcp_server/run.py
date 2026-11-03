"""stdio 入口：`python -m app.mcp_server.run` 启动 MCP 课程服务。"""
from __future__ import annotations

from app.mcp_server.course_mcp import build_server


def main() -> None:
    server = build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()