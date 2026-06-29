#!/usr/bin/env python3
"""TAPD 需求自动获取、测试用例生成与导入 CLI。"""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.table import Table

from tapd_testcase.config import AppConfig
from tapd_testcase.pipeline import TapdTestCasePipeline

console = Console()


@click.group()
@click.option("--config", "-c", default="config.yaml", help="配置文件路径")
@click.option("--env", default=".env", help="环境变量文件路径")
@click.pass_context
def cli(ctx: click.Context, config: str, env: str) -> None:
    """TAPD 测试用例自动生成与导入工具。"""
    ctx.ensure_object(dict)
    try:
        ctx.obj["config"] = AppConfig.load(config_path=config, env_path=env)
    except ValueError as exc:
        console.print(f"[red]配置错误:[/red] {exc}")
        sys.exit(1)


@cli.command("list-stories")
@click.pass_context
def list_stories(ctx: click.Context) -> None:
    """列出符合条件的需求。"""
    pipeline = TapdTestCasePipeline(ctx.obj["config"])
    stories = pipeline.fetch_stories()

    table = Table(title=f"需求列表（共 {len(stories)} 条）")
    table.add_column("ID", style="cyan")
    table.add_column("标题")
    table.add_column("状态")
    table.add_column("负责人")

    for story in stories:
        table.add_row(story.id, story.name[:50], story.status, story.owner)

    console.print(table)


@cli.command("generate")
@click.option("--story-id", multiple=True, help="指定需求 ID，可多次传入")
@click.option("--output", "-o", default=None, help="输出目录，覆盖配置")
@click.pass_context
def generate(ctx: click.Context, story_id: tuple[str, ...], output: str | None) -> None:
    """仅生成测试用例预览（默认 dry-run，不写入 TAPD）。"""
    config: AppConfig = ctx.obj["config"]
    config.import_.dry_run = True
    if output:
        config.import_.output_dir = output
    if story_id:
        config.story_filter.story_ids = list(story_id)

    pipeline = TapdTestCasePipeline(config)
    results = pipeline.run()
    _print_results(results, dry_run=True)


@cli.command("import")
@click.option("--story-id", multiple=True, help="指定需求 ID，可多次传入")
@click.option("--dry-run", is_flag=True, help="仅预览，不写入 TAPD")
@click.pass_context
def import_cmd(ctx: click.Context, story_id: tuple[str, ...], dry_run: bool) -> None:
    """生成测试用例并导入 TAPD。"""
    config: AppConfig = ctx.obj["config"]
    config.import_.dry_run = dry_run
    if story_id:
        config.story_filter.story_ids = list(story_id)

    pipeline = TapdTestCasePipeline(config)
    results = pipeline.run()
    _print_results(results, dry_run=dry_run)


@cli.command("run")
@click.option("--story-id", multiple=True, help="指定需求 ID，可多次传入")
@click.option("--dry-run", is_flag=True, help="仅预览，不写入 TAPD")
@click.pass_context
def run(ctx: click.Context, story_id: tuple[str, ...], dry_run: bool) -> None:
    """执行完整流程：获取需求 → 生成用例 → 导入 TAPD。"""
    config: AppConfig = ctx.obj["config"]
    config.import_.dry_run = dry_run
    if story_id:
        config.story_filter.story_ids = list(story_id)

    pipeline = TapdTestCasePipeline(config)
    results = pipeline.run()
    _print_results(results, dry_run=dry_run)


def _print_results(results: list, dry_run: bool) -> None:
    if not results:
        console.print("[yellow]未找到符合条件的需求。[/yellow]")
        return

    table = Table(title="处理结果")
    table.add_column("需求 ID")
    table.add_column("需求标题")
    table.add_column("生成数")
    table.add_column("导入数")
    table.add_column("备注")

    for r in results:
        note = "; ".join(r.errors) if r.errors else ("预览模式" if dry_run else "成功")
        table.add_row(r.story_id, r.story_name[:40], str(r.generated_count), str(r.imported_count), note[:80])

    console.print(table)

    summary = {
        "stories": len(results),
        "generated": sum(r.generated_count for r in results),
        "imported": sum(r.imported_count for r in results),
        "dry_run": dry_run,
    }
    console.print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    cli()
