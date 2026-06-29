from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from tapd_testcase.config import GeneratorConfig
from tapd_testcase.exporter import export_tcases_csv
from tapd_testcase.generator.rule_generator import RuleBasedGenerator
from tapd_testcase.generator.story_1029894_cases import generate_story_1029894_cases
from tapd_testcase.models import Story, TestCase
from tapd_testcase.tapd_client import TapdClient

CUSTOM_GENERATORS: dict[str, Callable[[Story], list[TestCase]]] = {
    "1029894": generate_story_1029894_cases,
    "1146254053001029894": generate_story_1029894_cases,
}


@dataclass
class GenerateRequest:
    client_id: str
    client_secret: str
    workspace_id: str
    story_id: str
    creator: str
    category: str = ""
    generator_mode: str = "auto"  # auto | rule | custom
    max_cases_per_story: int = 8
    import_to_tapd: bool = True
    output_dir: str = "output/web"


@dataclass
class GenerateResult:
    success: bool
    story_id: str = ""
    story_short_id: str = ""
    story_name: str = ""
    creator: str = ""
    generated_count: int = 0
    imported_count: int = 0
    tcase_ids: list[str] = field(default_factory=list)
    csv_path: str = ""
    json_path: str = ""
    test_cases: list[dict] = field(default_factory=list)
    error: str = ""


def resolve_full_story_id(client: TapdClient, workspace_id: str, story_id: str) -> str:
    story_id = story_id.strip()
    if len(story_id) > 10:
        return story_id
    stories = client.get_stories(workspace_id, limit=200, fields="id,name")
    for story in stories:
        if story.id.endswith(story_id):
            return story.id
    raise ValueError(f"未找到短 ID 为 {story_id} 的需求，请确认项目 ID 与需求 ID 是否正确")


def pick_generator(req: GenerateRequest, story: Story) -> Callable[[Story], list[TestCase]]:
    short_key = req.story_id.strip()
    full_key = story.id

    if req.generator_mode == "custom" or req.generator_mode == "auto":
        custom = CUSTOM_GENERATORS.get(short_key) or CUSTOM_GENERATORS.get(full_key)
        if custom:
            return custom

    if req.generator_mode == "custom":
        raise ValueError(f"需求 {req.story_id} 暂无专项用例模板，请改用「规则生成」模式")

    rule = RuleBasedGenerator(
        GeneratorConfig(
            max_cases_per_story=req.max_cases_per_story,
            include_story_id_in_name=True,
        )
    )
    return rule.generate


def run_generate(req: GenerateRequest) -> GenerateResult:
    try:
        client = TapdClient(
            api_base="https://api.tapd.cn",
            client_id=req.client_id,
            client_secret=req.client_secret,
        )
        full_id = resolve_full_story_id(client, req.workspace_id, req.story_id)
        stories = client.get_stories(
            req.workspace_id,
            story_ids=[full_id],
            fields="id,name,description,test_focus,status,priority_label,owner,workspace_id",
        )
        if not stories:
            raise ValueError(f"未找到需求 {req.story_id}")

        story = stories[0]
        short_id = req.story_id.strip() if len(req.story_id.strip()) <= 10 else story.id[-7:]
        generator = pick_generator(req, story)
        cases = generator(story)

        output_dir = Path(req.output_dir) / f"story_{short_id}"
        category = req.category.strip() or story.name
        csv_path = export_tcases_csv(
            cases,
            output_dir / f"测试用例_需求{short_id}_{story.name}.csv",
            category=category,
            story_id=short_id,
            creator=req.creator,
        )

        json_path = output_dir / f"测试用例_需求{short_id}_{story.name}.json"
        case_dicts = [
            {
                "name": c.name,
                "precondition": c.precondition,
                "steps": c.steps,
                "expectation": c.expectation,
                "type": c.type,
                "priority": c.priority,
            }
            for c in cases
        ]
        json_path.write_text(
            json.dumps(
                {
                    "story": {"id": story.id, "short_id": short_id, "name": story.name},
                    "creator": req.creator,
                    "test_cases": case_dicts,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        result = GenerateResult(
            success=True,
            story_id=story.id,
            story_short_id=short_id,
            story_name=story.name,
            creator=req.creator,
            generated_count=len(cases),
            csv_path=str(csv_path.resolve()),
            json_path=str(json_path.resolve()),
            test_cases=case_dicts,
        )

        if req.import_to_tapd:
            payloads = [
                {
                    "workspace_id": req.workspace_id,
                    "name": c.name,
                    "precondition": c.precondition,
                    "steps": c.steps,
                    "expectation": c.expectation,
                    "type": c.type,
                    "priority": c.priority,
                    "status": "normal",
                    "creator": req.creator,
                }
                for c in cases
            ]
            created = client.batch_create_tcases(payloads)
            result.imported_count = len(created)
            result.tcase_ids = [str(item.get("id", "")) for item in created if item.get("id")]

        return result
    except Exception as exc:
        return GenerateResult(success=False, error=str(exc))
