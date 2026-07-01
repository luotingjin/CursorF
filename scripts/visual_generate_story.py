#!/usr/bin/env python3
"""可视化浏览器操作：在 Web 页面生成用例并导入 TAPD。"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)


def run(story_id: str, base_url: str = "http://127.0.0.1:8080", slowmo: int = 400) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome", slow_mo=slowmo)
        page = browser.new_page(locale="zh-CN")
        page.goto(base_url)

        expect(page).to_have_title("TAPD 测试用例生成器")
        page.locator('[name="story_id"]').fill(story_id)

        import_checkbox = page.locator('[name="import_to_tapd"]')
        if not import_checkbox.is_checked():
            import_checkbox.check()

        print(f"正在生成需求 {story_id} 的测试用例并导入 TAPD...")
        page.locator("#submitBtn").click()

        expect(page.locator("#resultCard")).to_be_visible(timeout=120_000)
        expect(page.locator("#submitBtn")).to_have_text("生成测试用例", timeout=120_000)

        error = page.locator("#resultError")
        if error.is_visible():
            msg = error.inner_text().strip()
            browser.close()
            raise SystemExit(f"生成失败：{msg}")

        summary = page.locator("#resultSummary").inner_text()
        generated = _extract_stat(summary, "生成数")
        imported = _extract_stat(summary, "导入数")
        story_name = page.locator("#resultSummary strong").first.inner_text()

        print(f"需求：{story_name}")
        print(f"生成数：{generated}")
        print(f"导入 TAPD 数：{imported}")

        case_count = page.locator("#casesBody tr").count()
        print(f"页面展示用例：{case_count} 条")

        print("浏览器将保持 15 秒供查看结果...")
        time.sleep(15)
        browser.close()


def _extract_stat(text: str, label: str) -> str:
    pattern = rf"{re.escape(label)}\s*([\d]+)"
    match = re.search(pattern, text.replace("\n", " "))
    return match.group(1) if match else "?"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="可视化生成并导入 TAPD 测试用例")
    parser.add_argument("story_id", help="需求 ID（支持短 ID）")
    parser.add_argument("--url", default="http://127.0.0.1:8080", help="Web 页面地址")
    parser.add_argument("--slowmo", type=int, default=400, help="操作间隔毫秒")
    args = parser.parse_args()
    run(args.story_id, base_url=args.url, slowmo=args.slowmo)
