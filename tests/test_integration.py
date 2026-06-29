"""集成测试：使用 Mock TAPD API 验证完整流水线。"""

import json
import unittest
from unittest.mock import MagicMock, patch

from tapd_testcase.config import AppConfig, GeneratorConfig, ImportConfig, StoryFilterConfig, TapdConfig
from tapd_testcase.importer import TestCaseImporter
from tapd_testcase.models import Story
from tapd_testcase.pipeline import TapdTestCasePipeline
from tapd_testcase.tapd_client import TapdClient


def make_config(**overrides) -> AppConfig:
    config = AppConfig(
        tapd=TapdConfig(
            api_base="https://api.tapd.cn",
            workspace_id="10158231",
            client_id="test_client",
            client_secret="test_secret",
            creator="tester",
        ),
        story_filter=StoryFilterConfig(story_ids=["1010104801869398419"], limit=1, max_pages=1),
        generator=GeneratorConfig(mode="rule", max_cases_per_story=5),
        import_=ImportConfig(dry_run=False, output_dir="./output_test"),
    )
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


MOCK_STORY_RESPONSE = {
    "status": 1,
    "data": [
        {
            "Story": {
                "id": "1010104801869398419",
                "name": "用户登录功能",
                "description": "<p>验收标准</p><ul><li>正确账号可登录</li><li>错误密码有提示</li></ul>",
                "test_focus": "密码强度校验",
                "status": "planning",
                "priority_label": "高",
                "owner": "tester",
                "workspace_id": "10158231",
            }
        }
    ],
    "info": "success",
}

MOCK_BATCH_CREATE_RESPONSE = {
    "status": 1,
    "data": [
        {"Tcase": {"id": "1010158231077224795", "name": "case1"}},
        {"Tcase": {"id": "1010158231077224796", "name": "case2"}},
        {"Tcase": {"id": "1010158231077224797", "name": "case3"}},
    ],
    "info": "success",
}


class TestTapdClient(unittest.TestCase):
    @patch("tapd_testcase.tapd_client.requests.Session.request")
    def test_get_stories_parses_response(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_STORY_RESPONSE
        mock_request.return_value = mock_resp

        client = TapdClient("https://api.tapd.cn", client_id="id", client_secret="secret")
        stories = client.get_stories("10158231", story_ids=["1010104801869398419"])

        self.assertEqual(len(stories), 1)
        self.assertEqual(stories[0].name, "用户登录功能")
        self.assertEqual(stories[0].id, "1010104801869398419")

    @patch("tapd_testcase.tapd_client.requests.Session.request")
    def test_batch_create_tcases(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_BATCH_CREATE_RESPONSE
        mock_request.return_value = mock_resp

        client = TapdClient("https://api.tapd.cn", client_id="id", client_secret="secret")
        cases = [{"workspace_id": "10158231", "name": "test case"}]
        result = client.batch_create_tcases(cases)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["id"], "1010158231077224795")


class TestPipelineIntegration(unittest.TestCase):
    @patch("tapd_testcase.tapd_client.requests.Session.request")
    def test_full_pipeline_import(self, mock_request):
        """模拟完整流程：拉需求 → 生成用例 → 批量导入。"""

        def side_effect(method, url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            if "/stories" in url and method == "GET":
                resp.json.return_value = MOCK_STORY_RESPONSE
            elif "/tcases/batch_save" in url:
                resp.json.return_value = MOCK_BATCH_CREATE_RESPONSE
            else:
                resp.json.return_value = {"status": 1, "data": [], "info": "success"}
            return resp

        mock_request.side_effect = side_effect

        config = make_config()
        pipeline = TapdTestCasePipeline(config)
        results = pipeline.run()

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.story_id, "1010104801869398419")
        self.assertGreater(result.generated_count, 0)
        self.assertEqual(result.imported_count, 3)
        self.assertEqual(len(result.tcase_ids), 3)

    @patch("tapd_testcase.tapd_client.requests.Session.request")
    def test_dry_run_skips_import(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_STORY_RESPONSE
        mock_request.return_value = mock_resp

        config = make_config()
        config.import_.dry_run = True
        pipeline = TapdTestCasePipeline(config)
        results = pipeline.run()

        self.assertEqual(results[0].imported_count, 0)
        # batch_save 不应被调用
        called_urls = [str(call) for call in mock_request.call_args_list]
        batch_calls = [u for u in called_urls if "batch_save" in u]
        self.assertEqual(len(batch_calls), 0)


class TestConfigValidation(unittest.TestCase):
    def test_missing_workspace_raises(self):
        config = make_config()
        config.tapd.workspace_id = ""
        with self.assertRaises(ValueError):
            config.validate()

    def test_missing_credentials_raises(self):
        config = make_config()
        config.tapd.client_id = None
        config.tapd.client_secret = None
        config.tapd.access_token = None
        with self.assertRaises(ValueError):
            config.validate()


class TestCLIConfigError(unittest.TestCase):
    def test_cli_without_config_exits(self):
        import subprocess

        result = subprocess.run(
            ["python3", "main.py", "-c", "nonexistent.yaml", "list-stories"],
            cwd="/workspace",
            capture_output=True,
            text=True,
        )
        # 无凭证时应报错退出
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
