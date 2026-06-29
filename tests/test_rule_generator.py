"""规则生成器单元测试。"""

import unittest

from tapd_testcase.config import GeneratorConfig
from tapd_testcase.generator.rule_generator import RuleBasedGenerator, extract_acceptance_criteria, strip_html
from tapd_testcase.models import Story


class TestRuleGenerator(unittest.TestCase):
    def test_strip_html(self):
        html = "<p>Hello <b>World</b></p><ul><li>Item1</li></ul>"
        text = strip_html(html)
        self.assertIn("Hello", text)
        self.assertIn("Item1", text)
        self.assertNotIn("<p>", text)

    def test_extract_acceptance_criteria(self):
        text = """需求说明
验收标准
- 用户可以登录
- 密码错误时提示
1. 支持记住密码
"""
        items = extract_acceptance_criteria(text)
        self.assertGreaterEqual(len(items), 2)
        self.assertTrue(any("登录" in x for x in items))

    def test_generate_cases(self):
        story = Story(
            id="123",
            name="用户登录功能",
            description="验收标准\n- 正确账号可登录\n- 错误密码提示",
            test_focus="密码强度校验",
        )
        gen = RuleBasedGenerator(GeneratorConfig(max_cases_per_story=5))
        cases = gen.generate(story)
        self.assertGreaterEqual(len(cases), 2)
        self.assertTrue(any("主流程" in c.name for c in cases))
        self.assertTrue(all(c.story_id == "123" for c in cases))


if __name__ == "__main__":
    unittest.main()
