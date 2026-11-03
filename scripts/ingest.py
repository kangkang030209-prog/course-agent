"""导入示例资料到向量库：`python scripts/ingest.py`。"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# 确保可从项目根导入 app（脚本位于 scripts/ 子目录）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="导入课程资料到 Chroma 知识库")
    parser.add_argument(
        "--force", action="store_true", help="重建向量库集合（清除旧数据）"
    )
    parser.add_argument("--verbose", action="store_true", help="显示日志")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from app.rag.ingest import ingest

    try:
        n = ingest(force_rebuild=args.force)
        print(f"入库完成，写入 {n} 个文本块。")
        return 0
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).exception("入库失败")
        print(f"入库失败: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())