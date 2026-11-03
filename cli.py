"""命令行交互入口：`python cli.py`。

仓库使用 stdin/stdout 的简单问答循环。
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys


async def _run(args: argparse.Namespace) -> int:
    from app.agent.service import CourseAssistant

    try:
        assistant = CourseAssistant(use_mcp=not args.no_mcp)
        await assistant.build()
    except Exception as exc:  # noqa: BLE001
        print(f"[错误] 初始化助手失败: {exc}", file=sys.stderr)
        return 1

    try:
        if args.once:
            print(await assistant.aask(args.once))
            return 0

        print("课程智能助手已就绪（输入 'exit' 退出，'reload' 重新导入知识库）。")
        while True:
            try:
                question = input("你> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            q = question.strip()
            if not q:
                continue
            if q.lower() in ("exit", "quit", "退出"):
                break
            if q.lower() == "reload":
                from app.rag.ingest import ingest

                try:
                    n = ingest()
                    print(f"[知识库] 已导入 {n} 个文本块。")
                except Exception as exc:  # noqa: BLE001
                    print(f"[知识库] 导入失败: {exc}")
                continue
            try:
                answer = await assistant.aask(q)
                print(f"助手> {answer}\n")
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                if "401" in msg or "Authentication" in msg or "invalid" in msg.lower():
                    print(
                        "[错误] DeepSeek API Key 无效或缺失。请在项目 .env 中填入有效的 "
                        "DEEPSEEK_API_KEY 后重启。",
                        file=sys.stderr,
                    )
                else:
                    print(f"[错误] {exc}", file=sys.stderr)
    finally:
        await assistant.aclose()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="课程智能助手 CLI")
    parser.add_argument("--verbose", action="store_true", help="输出日志")
    parser.add_argument(
        "--once",
        metavar="问题",
        help="单次提问后退出（非交互模式，便于脚本调用）",
    )
    parser.add_argument(
        "--no-mcp", action="store_true", help="禁用 MCP 工具，仅用 RAG"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())