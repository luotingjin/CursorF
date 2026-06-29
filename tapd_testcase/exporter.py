from __future__ import annotations

import csv
from pathlib import Path

from tapd_testcase.models import TestCase

# TAPD 测试用例批量导入标准字段（与官方 Excel/CSV 模板一致）
TAPD_CSV_HEADERS = [
    "用例目录",
    "用例名称",
    "需求ID",
    "前置条件",
    "用例步骤",
    "预期结果",
    "用例类型",
    "用例状态",
    "用例等级",
    "创建人",
    "测试结果",
    "备注说明",
]


def testcase_to_tapd_row(
    case: TestCase,
    *,
    category: str = "未规划目录",
    story_id: str,
    creator: str = "",
    remark: str = "",
) -> list[str]:
    return [
        category,
        case.name,
        story_id,
        case.precondition,
        case.steps,
        case.expectation,
        case.type,
        "正常",
        case.priority,
        creator,
        "",
        remark,
    ]


def export_tcases_csv(
    cases: list[TestCase],
    output_path: str | Path,
    *,
    category: str = "未规划目录",
    story_id: str,
    creator: str = "",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(TAPD_CSV_HEADERS)
        for case in cases:
            writer.writerow(
                testcase_to_tapd_row(
                    case,
                    category=category,
                    story_id=story_id,
                    creator=creator,
                    remark=f"关联需求：{case.story_name}" if case.story_name else "",
                )
            )
    return path
