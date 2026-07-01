"""TAPD 测试用例生成器 Web 页面 E2E 测试。"""

from __future__ import annotations

import json

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

MOCK_GENERATE_RESPONSE = {
    "success": True,
    "story_id": "1010104801869398419",
    "story_short_id": "1869398419",
    "story_name": "用户登录功能",
    "creator": "测试员",
    "generated_count": 5,
    "imported_count": 0,
    "tcase_ids": [],
    "csv_download": "/download?path=/tmp/test.csv",
    "test_cases": [
        {"name": "主流程验证", "priority": "高", "type": "功能测试"},
        {"name": "验收项1", "priority": "中", "type": "功能测试"},
    ],
}


def test_home_page_loads(page: Page, base_url: str) -> None:
    page.goto(base_url)

    expect(page).to_have_title("TAPD 测试用例生成器")
    expect(page.get_by_role("heading", name="TAPD 测试用例生成器")).to_be_visible()
    expect(page.locator('[name="client_id"]')).to_be_visible()
    expect(page.locator('[name="story_id"]')).to_be_visible()
    expect(page.locator("#resetBtn")).to_be_visible()
    expect(page.locator('[name="max_cases_per_story"]')).to_have_count(0)


def test_reset_clears_fields_and_hides_results(page: Page, base_url: str) -> None:
    page.goto(base_url)

    story_input = page.locator('[name="story_id"]')
    story_input.fill("1029894")
    page.locator('[name="category"]').fill("自定义目录")

    page.evaluate(
        """() => {
            document.getElementById('resultCard').hidden = false;
            document.getElementById('resultSummary').innerHTML = '<p>mock result</p>';
        }"""
    )
    expect(page.locator("#resultCard")).to_be_visible()

    page.locator("#resetBtn").click()

    expect(story_input).to_have_value("")
    expect(page.locator('[name="category"]')).to_have_value("")
    expect(page.locator("#resultCard")).to_be_hidden()


def test_validation_shows_error_without_story_id(page: Page, base_url: str) -> None:
    page.goto(base_url)

    page.locator("#generateForm").evaluate("form => { form.noValidate = true; }")
    page.locator('[name="story_id"]').fill("")
    page.locator("#submitBtn").click()

    expect(page.locator("#resultCard")).to_be_visible()
    expect(page.locator("#resultError")).to_be_visible()
    expect(page.locator("#resultError")).to_contain_text("请填写必填项")


def test_generate_success_with_mocked_api(page: Page, base_url: str) -> None:
    def handle_generate(route, request):
        if request.method != "POST":
            route.continue_()
            return
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(MOCK_GENERATE_RESPONSE, ensure_ascii=False),
        )

    page.route("**/api/generate", handle_generate)
    page.goto(base_url)

    page.locator('[name="client_id"]').fill("tapd-app-test")
    page.locator('[name="client_secret"]').fill("secret-test")
    page.locator('[name="workspace_id"]').fill("10158231")
    page.locator('[name="story_id"]').fill("1869398419")
    page.locator('[name="creator"]').fill("测试员")
    page.locator('[name="import_to_tapd"]').uncheck()

    page.locator("#submitBtn").click()

    expect(page.locator("#resultError")).to_be_hidden()
    expect(page.locator("#resultSummary")).to_contain_text("用户登录功能")
    expect(page.locator("#resultSummary")).to_contain_text("5")
    expect(page.locator("#casesBody tr")).to_have_count(2)
    expect(page.locator("#downloadActions")).to_be_visible()


def test_generate_failure_shows_error(page: Page, base_url: str) -> None:
    def handle_generate(route, request):
        route.fulfill(
            status=400,
            content_type="application/json",
            body=json.dumps({"success": False, "error": "未找到需求 9999999"}, ensure_ascii=False),
        )

    page.route("**/api/generate", handle_generate)
    page.goto(base_url)

    page.locator('[name="client_id"]').fill("tapd-app-test")
    page.locator('[name="client_secret"]').fill("secret-test")
    page.locator('[name="workspace_id"]').fill("10158231")
    page.locator('[name="story_id"]').fill("9999999")
    page.locator('[name="creator"]').fill("测试员")
    page.locator("#submitBtn").click()

    expect(page.locator("#resultError")).to_be_visible()
    expect(page.locator("#resultError")).to_contain_text("未找到需求")
