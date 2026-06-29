from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Story:
    """TAPD 需求。"""

    id: str
    name: str
    description: str = ""
    test_focus: str = ""
    status: str = ""
    priority: str = ""
    owner: str = ""
    workspace_id: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_tapd(cls, data: dict[str, Any]) -> Story:
        story = data.get("Story", data)
        return cls(
            id=str(story.get("id", "")),
            name=str(story.get("name", "")),
            description=str(story.get("description") or ""),
            test_focus=str(story.get("test_focus") or ""),
            status=str(story.get("status") or ""),
            priority=str(story.get("priority_label") or story.get("priority") or ""),
            owner=str(story.get("owner") or ""),
            workspace_id=str(story.get("workspace_id") or ""),
            raw=story,
        )


@dataclass
class TestCase:
    """生成的测试用例。"""

    name: str
    precondition: str = ""
    steps: str = ""
    expectation: str = ""
    type: str = "功能测试"
    priority: str = "中"
    status: str = "normal"
    story_id: str = ""
    story_name: str = ""

    def to_tapd_payload(self, workspace_id: str, category_id: str = "-1", creator: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "workspace_id": workspace_id,
            "name": self.name,
            "precondition": self.precondition or None,
            "steps": self.steps or None,
            "expectation": self.expectation or None,
            "type": self.type,
            "priority": self.priority,
            "status": self.status,
            "category_id": category_id,
        }
        if creator:
            payload["creator"] = creator
        return {k: v for k, v in payload.items() if v is not None}


@dataclass
class ImportResult:
  story_id: str
  story_name: str
  generated_count: int
  imported_count: int
  tcase_ids: list[str] = field(default_factory=list)
  errors: list[str] = field(default_factory=list)
