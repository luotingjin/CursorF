from __future__ import annotations

import json
import re

from openai import OpenAI

from tapd_testcase.config import GeneratorConfig, LLMConfig
from tapd_testcase.generator.rule_generator import BaseGenerator, strip_html
from tapd_testcase.models import Story, TestCase


SYSTEM_PROMPT = """你是一名资深测试工程师。根据 TAPD 需求内容，生成结构化测试用例。
必须返回 JSON 数组，每个元素包含字段：
- name: 用例名称（简洁明确）
- precondition: 前置条件
- steps: 测试步骤（多行文本，用换行分隔）
- expectation: 预期结果
- type: 用例类型（功能测试/性能测试/安全性测试/其他）
- priority: 优先级（高/中/低）

要求：
1. 覆盖主流程、关键分支、异常与边界场景
2. 步骤可执行、预期可验证
3. 不要输出 JSON 以外的任何内容"""


class LLMGenerator(BaseGenerator):
    """使用 OpenAI 兼容 API 生成测试用例。"""

    def __init__(self, gen_config: GeneratorConfig, llm_config: LLMConfig):
        self.gen_config = gen_config
        self.llm_config = llm_config
        self.client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)

    def generate(self, story: Story) -> list[TestCase]:
        plain_desc = strip_html(story.description)
        user_prompt = (
            f"需求标题：{story.name}\n"
            f"需求 ID：{story.id}\n"
            f"测试重点：{story.test_focus or '无'}\n"
            f"优先级：{story.priority or '无'}\n"
            f"详细描述：\n{plain_desc or '无'}\n\n"
            f"请生成不超过 {self.gen_config.max_cases_per_story} 条测试用例。"
        )

        response = self.client.chat.completions.create(
            model=self.llm_config.model,
            temperature=self.llm_config.temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or "[]"
        raw_cases = self._parse_json_array(content)

        cases: list[TestCase] = []
        prefix = f"[{story.id}] " if self.gen_config.include_story_id_in_name else ""
        for item in raw_cases[: self.gen_config.max_cases_per_story]:
            name = str(item.get("name", "未命名用例"))
            if prefix and not name.startswith(prefix):
                name = f"{prefix}{name}"
            cases.append(
                TestCase(
                    name=name,
                    precondition=str(item.get("precondition", "")),
                    steps=str(item.get("steps", "")),
                    expectation=str(item.get("expectation", "")),
                    type=str(item.get("type", self.gen_config.default_type)),
                    priority=str(item.get("priority", self.gen_config.default_priority)),
                    story_id=story.id,
                    story_name=story.name,
                )
            )
        return cases

    def _parse_json_array(self, content: str) -> list[dict]:
        content = content.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if fence:
            content = fence.group(1).strip()
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        return []
