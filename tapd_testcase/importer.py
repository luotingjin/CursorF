from __future__ import annotations

import json
from pathlib import Path

from tapd_testcase.config import AppConfig
from tapd_testcase.models import ImportResult, Story, TestCase
from tapd_testcase.tapd_client import TapdClient


class TestCaseImporter:
    def __init__(self, client: TapdClient, config: AppConfig):
        self.client = client
        self.config = config

    def save_preview(self, story: Story, cases: list[TestCase], output_dir: str) -> Path:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        file_path = out / f"story_{story.id}_tcases.json"
        payload = {
            "story": {
                "id": story.id,
                "name": story.name,
                "status": story.status,
            },
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
        }
        file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return file_path

    def import_cases(self, story: Story, cases: list[TestCase]) -> ImportResult:
        result = ImportResult(
            story_id=story.id,
            story_name=story.name,
            generated_count=len(cases),
            imported_count=0,
        )

        preview_path = self.save_preview(story, cases, self.config.import_.output_dir)
        result.errors.append(f"预览已保存: {preview_path}")

        if self.config.import_.dry_run:
            result.imported_count = 0
            return result

        tapd = self.config.tapd
        payloads = [
            c.to_tapd_payload(tapd.workspace_id, tapd.category_id, tapd.creator)
            for c in cases
        ]

        created: list[dict] = []
        batch_size = 50
        for i in range(0, len(payloads), batch_size):
            try:
                batch = self.client.batch_create_tcases(payloads[i : i + batch_size])
                created.extend(batch)
            except Exception as exc:
                result.errors.append(f"批量导入失败: {exc}")

        result.imported_count = len(created)
        result.tcase_ids = [str(item.get("id", "")) for item in created if item.get("id")]

        if self.config.import_.link_to_story and result.tcase_ids:
            creator = tapd.creator or "api"
            try:
                self.client.link_story_to_test_plan(
                    tapd.workspace_id,
                    str(tapd.test_plan_id),
                    [story.id],
                    creator,
                )
                self.client.link_tcases_to_test_plan(
                    tapd.workspace_id,
                    str(tapd.test_plan_id),
                    result.tcase_ids,
                    creator,
                )
            except Exception as exc:
                result.errors.append(f"关联测试计划失败: {exc}")

        return result
