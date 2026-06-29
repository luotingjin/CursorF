from __future__ import annotations

from tapd_testcase.config import AppConfig
from tapd_testcase.generator.llm_generator import LLMGenerator
from tapd_testcase.generator.rule_generator import BaseGenerator, RuleBasedGenerator
from tapd_testcase.importer import TestCaseImporter
from tapd_testcase.models import ImportResult, Story
from tapd_testcase.tapd_client import TapdClient


class TapdTestCasePipeline:
    """从 TAPD 拉取需求 → 生成用例 → 导入 TAPD 的完整流水线。"""

    def __init__(self, config: AppConfig):
        config.validate()
        self.config = config
        self.client = TapdClient(
            api_base=config.tapd.api_base,
            client_id=config.tapd.client_id,
            client_secret=config.tapd.client_secret,
            access_token=config.tapd.access_token,
        )
        self.generator = self._build_generator()
        self.importer = TestCaseImporter(self.client, config)

    def _build_generator(self) -> BaseGenerator:
        if self.config.generator.mode == "llm":
            return LLMGenerator(self.config.generator, self.config.llm)
        return RuleBasedGenerator(self.config.generator)

    def fetch_stories(self) -> list[Story]:
        sf = self.config.story_filter
        tapd = self.config.tapd
        return list(
            self.client.iter_stories(
                tapd.workspace_id,
                story_ids=sf.story_ids or None,
                iteration_id=sf.iteration_id,
                status=sf.status,
                limit=sf.limit,
                max_pages=sf.max_pages,
            )
        )

    def process_story(self, story: Story) -> ImportResult:
        cases = self.generator.generate(story)
        return self.importer.import_cases(story, cases)

    def run(self) -> list[ImportResult]:
        stories = self.fetch_stories()
        if not stories:
            return []
        return [self.process_story(story) for story in stories]
