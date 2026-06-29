from __future__ import annotations

import re
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from tapd_testcase.config import GeneratorConfig
from tapd_testcase.models import Story, TestCase


class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, story: Story) -> list[TestCase]:
        raise NotImplementedError


def strip_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_acceptance_criteria(text: str) -> list[str]:
    """从需求描述中提取验收标准、测试点等条目。"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    items: list[str] = []

    section_keywords = ("验收标准", "验收条件", "测试点", "测试重点", "AC", "acceptance")
    in_section = False

    for line in lines:
        if any(kw in line for kw in section_keywords):
            in_section = True
            continue
        if in_section and re.match(r"^#{1,3}\s", line):
            break

        bullet_match = re.match(r"^[-*•\d]+[.)）]?\s*(.+)$", line)
        if bullet_match:
            items.append(bullet_match.group(1).strip())
        elif in_section and len(line) > 4:
            items.append(line)

    if not items:
        for line in lines:
            if re.match(r"^[-*•\d]+[.)）]?\s*(.+)$", line):
                items.append(re.sub(r"^[-*•\d]+[.)）]?\s*", "", line).strip())

    return [x for x in items if len(x) >= 4][:10]


class RuleBasedGenerator(BaseGenerator):
    """基于需求内容规则生成测试用例，无需外部 LLM。"""

    def __init__(self, config: GeneratorConfig):
        self.config = config

    def generate(self, story: Story) -> list[TestCase]:
        plain_desc = strip_html(story.description)
        criteria = extract_acceptance_criteria(plain_desc)
        if story.test_focus:
            criteria.extend([x.strip() for x in re.split(r"[\n;；]", story.test_focus) if x.strip()])

        seen: set[str] = set()
        unique_criteria: list[str] = []
        for item in criteria:
            key = item[:80]
            if key not in seen:
                seen.add(key)
                unique_criteria.append(item)

        cases: list[TestCase] = []
        prefix = f"[{story.id}] " if self.config.include_story_id_in_name else ""

        cases.append(
            TestCase(
                name=f"{prefix}{story.name} - 主流程验证",
                precondition="系统已部署且测试账号具备相应权限",
                steps=self._build_main_steps(story.name, plain_desc),
                expectation="功能按需求描述正常工作，核心流程可顺利完成",
                type=self.config.default_type,
                priority="高",
                story_id=story.id,
                story_name=story.name,
            )
        )

        for idx, criterion in enumerate(unique_criteria[: self.config.max_cases_per_story - 2], start=1):
            cases.append(
                TestCase(
                    name=f"{prefix}{story.name} - 验收项{idx}: {criterion[:30]}",
                    precondition="满足该验收项所需的前置数据与环境",
                    steps=f"1. 按需求准备测试数据\n2. 执行与「{criterion}」相关的操作\n3. 检查结果",
                    expectation=f"满足验收要求：{criterion}",
                    type=self.config.default_type,
                    priority=self.config.default_priority,
                    story_id=story.id,
                    story_name=story.name,
                )
            )

        cases.append(
            TestCase(
                name=f"{prefix}{story.name} - 异常与边界验证",
                precondition="系统可访问",
                steps="1. 输入空值、非法格式或越界参数\n2. 在无权限/未登录状态下尝试操作\n3. 模拟网络中断或重复提交",
                expectation="系统给出明确错误提示，不产生脏数据，核心功能不受影响",
                type=self.config.default_type,
                priority=self.config.default_priority,
                story_id=story.id,
                story_name=story.name,
            )
        )

        return cases[: self.config.max_cases_per_story]

    def _build_main_steps(self, name: str, description: str) -> str:
        summary = description[:300].replace("\n", " ") if description else name
        return (
            f"1. 登录系统并进入相关功能模块\n"
            f"2. 按需求「{name}」执行主流程操作\n"
            f"3. 核对页面展示与业务结果\n"
            f"参考需求：{summary}"
        )
