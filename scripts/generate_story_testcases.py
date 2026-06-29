#!/usr/bin/env python3
"""按指定需求生成测试用例 CSV，并可选导入 TAPD。"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from tapd_testcase.service import GenerateRequest, run_generate

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成需求测试用例并导入 TAPD")
    parser.add_argument("--env", default=".env")
    parser.add_argument("--story-id", required=True, help="需求 ID（支持短 ID）")
    parser.add_argument("--creator", required=True, help="用例创建人（固定）")
    parser.add_argument("--output-dir", default=None, help="输出目录")
    parser.add_argument("--category", default="", help="用例目录")
    parser.add_argument("--no-import", action="store_true", help="仅生成文件，不导入 TAPD")
    args = parser.parse_args()

    load_dotenv(args.env)
    client_id = os.getenv("TAPD_CLIENT_ID")
    client_secret = os.getenv("TAPD_CLIENT_SECRET")
    workspace_id = os.getenv("TAPD_WORKSPACE_ID")
    if not all([client_id, client_secret, workspace_id]):
        print("请配置 TAPD_CLIENT_ID、TAPD_CLIENT_SECRET、TAPD_WORKSPACE_ID", file=sys.stderr)
        return 1

    result = run_generate(
        GenerateRequest(
            client_id=client_id,
            client_secret=client_secret,
            workspace_id=workspace_id,
            story_id=args.story_id,
            creator=args.creator,
            category=args.category,
            import_to_tapd=not args.no_import,
            output_dir=args.output_dir or "testcases",
        )
    )

    if not result.success:
        print(result.error, file=sys.stderr)
        return 1

    print(f"需求: {result.story_name} ({result.story_id})")
    print(f"创建人: {result.creator}")
    print(f"生成用例: {result.generated_count} 条")
    print(f"CSV: {result.csv_path}")
    if result.imported_count:
        print(f"已导入 TAPD: {result.imported_count} 条")
        print(f"用例 ID 示例: {', '.join(result.tcase_ids[:3])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
