#!/usr/bin/env python3
"""按指定需求生成测试用例 CSV，并可选导入 TAPD。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from tapd_testcase.exporter import TAPD_CSV_HEADERS, export_tcases_csv
from tapd_testcase.generator.story_1029894_cases import generate_story_1029894_cases
from tapd_testcase.models import Story

STORY_GENERATORS = {
    "1029894": generate_story_1029894_cases,
    "1146254053001029894": generate_story_1029894_cases,
}


def resolve_full_story_id(client: tuple[str, str], workspace_id: str, story_id: str) -> str:
    if len(story_id) > 10:
        return story_id
    auth = client
    r = requests.get(
        "https://api.tapd.cn/stories",
        params={
            "workspace_id": workspace_id,
            "limit": 200,
            "fields": "id,name",
        },
        auth=auth,
        timeout=60,
    )
    r.raise_for_status()
    for item in r.json().get("data", []):
        full_id = item["Story"]["id"]
        if full_id.endswith(story_id):
            return full_id
    raise ValueError(f"未找到短 ID 为 {story_id} 的需求")


def fetch_story(client: tuple[str, str], workspace_id: str, story_id: str) -> Story:
    r = requests.get(
        "https://api.tapd.cn/stories",
        params={
            "workspace_id": workspace_id,
            "id": story_id,
            "fields": "id,name,description,test_focus,status,priority_label,owner,workspace_id",
        },
        auth=client,
        timeout=60,
    )
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        raise ValueError(f"未找到需求 {story_id}")
    return Story.from_tapd(data[0])


def import_to_tapd(client: tuple[str, str], workspace_id: str, cases: list[dict]) -> list[str]:
    r = requests.post(
        "https://api.tapd.cn/tcases/batch_save",
        json=cases,
        auth=client,
        timeout=60,
    )
    r.raise_for_status()
    body = r.json()
    if body.get("status") != 1:
        raise RuntimeError(f"导入失败: {body.get('info')}")
    return [item["Tcase"]["id"] for item in body.get("data", [])]


def main() -> int:
    parser = argparse.ArgumentParser(description="生成需求测试用例并导入 TAPD")
    parser.add_argument("--env", default=".env")
    parser.add_argument("--story-id", required=True, help="需求 ID（支持短 ID）")
    parser.add_argument("--story-short-id", help="CSV 中写入的需求短 ID")
    parser.add_argument("--creator", required=True, help="用例创建人（固定）")
    parser.add_argument("--output-dir", default=None, help="输出目录")
    parser.add_argument("--category", default=None, help="用例目录")
    parser.add_argument("--no-import", action="store_true", help="仅生成文件，不导入 TAPD")
    args = parser.parse_args()

    load_dotenv(args.env)
    client_id = os.getenv("TAPD_CLIENT_ID")
    client_secret = os.getenv("TAPD_CLIENT_SECRET")
    workspace_id = os.getenv("TAPD_WORKSPACE_ID")
    if not all([client_id, client_secret, workspace_id]):
        print("请配置 TAPD_CLIENT_ID、TAPD_CLIENT_SECRET、TAPD_WORKSPACE_ID", file=sys.stderr)
        return 1

    auth = (client_id, client_secret)
    short_id = args.story_short_id or args.story_id
    full_id = resolve_full_story_id(auth, workspace_id, args.story_id)
    story = fetch_story(auth, workspace_id, full_id)

    generator = STORY_GENERATORS.get(args.story_id) or STORY_GENERATORS.get(short_id)
    if not generator:
        print(f"暂不支持需求 {args.story_id} 的专项用例生成", file=sys.stderr)
        return 1

    cases = generator(story)
    output_dir = Path(args.output_dir or f"testcases/story_{short_id}")
    category = args.category or story.name

    csv_path = export_tcases_csv(
        cases,
        output_dir / f"测试用例_需求{short_id}_{story.name}.csv",
        category=category,
        story_id=short_id,
        creator=args.creator,
    )

    json_path = output_dir / f"测试用例_需求{short_id}_{story.name}.json"
    json_path.write_text(
        json.dumps(
            {
                "story": {"id": story.id, "short_id": short_id, "name": story.name},
                "creator": args.creator,
                "headers": TAPD_CSV_HEADERS,
                "test_cases": [
                    {
                        "name": c.name,
                        "precondition": c.precondition,
                        "steps": c.steps,
                        "expectation": c.expectation,
                        "type": c.type,
                        "priority": c.priority,
                    }
                    for c in cases
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"需求: {story.name} ({full_id})")
    print(f"创建人: {args.creator}")
    print(f"生成用例: {len(cases)} 条")
    print(f"CSV: {csv_path.resolve()}")

    if args.no_import:
        return 0

    payloads = [
        {
            "workspace_id": workspace_id,
            "name": c.name,
            "precondition": c.precondition,
            "steps": c.steps,
            "expectation": c.expectation,
            "type": c.type,
            "priority": c.priority,
            "status": "normal",
            "creator": args.creator,
        }
        for c in cases
    ]
    tcase_ids = import_to_tapd(auth, workspace_id, payloads)
    print(f"已导入 TAPD: {len(tcase_ids)} 条")
    print(f"用例 ID 示例: {', '.join(tcase_ids[:3])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
