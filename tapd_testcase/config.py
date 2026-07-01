from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class StoryFilterConfig:
    story_ids: list[str] = field(default_factory=list)
    iteration_id: str | None = None
    status: str | None = None
    limit: int = 30
    max_pages: int = 10


@dataclass
class GeneratorConfig:
    mode: str = "rule"
    max_cases_per_story: int = 0  # 0 表示不限制
    include_story_id_in_name: bool = True
    default_type: str = "功能测试"
    default_priority: str = "中"


@dataclass
class ImportConfig:
    link_to_story: bool = False
    dry_run: bool = False
    output_dir: str = "./output"


@dataclass
class LLMConfig:
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    temperature: float = 0.3


@dataclass
class TapdConfig:
    api_base: str = "https://api.tapd.cn"
    workspace_id: str = ""
    client_id: str | None = None
    client_secret: str | None = None
    access_token: str | None = None
    test_plan_id: str | None = None
    creator: str | None = None
    category_id: str = "-1"


@dataclass
class AppConfig:
    tapd: TapdConfig = field(default_factory=TapdConfig)
    story_filter: StoryFilterConfig = field(default_factory=StoryFilterConfig)
    generator: GeneratorConfig = field(default_factory=GeneratorConfig)
    import_: ImportConfig = field(default_factory=ImportConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)

    @classmethod
    def load(cls, config_path: str | None = None, env_path: str | None = None) -> AppConfig:
        if env_path is None:
            env_path = ".env"
        load_dotenv(env_path)

        data: dict[str, Any] = {}
        if config_path and Path(config_path).exists():
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        tapd_data = data.get("tapd", {})
        tapd = TapdConfig(
            api_base=os.getenv("TAPD_API_BASE", tapd_data.get("api_base", "https://api.tapd.cn")),
            workspace_id=os.getenv("TAPD_WORKSPACE_ID", str(tapd_data.get("workspace_id", ""))),
            client_id=os.getenv("TAPD_CLIENT_ID", tapd_data.get("client_id")),
            client_secret=os.getenv("TAPD_CLIENT_SECRET", tapd_data.get("client_secret")),
            access_token=os.getenv("TAPD_ACCESS_TOKEN", tapd_data.get("access_token")),
            test_plan_id=os.getenv("TAPD_TEST_PLAN_ID", tapd_data.get("test_plan_id")),
            creator=os.getenv("TAPD_CREATOR", tapd_data.get("creator")),
            category_id=str(tapd_data.get("category_id", "-1")),
        )

        sf = data.get("story_filter", {})
        story_filter = StoryFilterConfig(
            story_ids=[str(x) for x in sf.get("story_ids", [])],
            iteration_id=sf.get("iteration_id"),
            status=sf.get("status"),
            limit=int(sf.get("limit", 30)),
            max_pages=int(sf.get("max_pages", 10)),
        )

        gen = data.get("generator", {})
        generator = GeneratorConfig(
            mode=gen.get("mode", "rule"),
            max_cases_per_story=int(gen.get("max_cases_per_story", 0)),
            include_story_id_in_name=bool(gen.get("include_story_id_in_name", True)),
            default_type=gen.get("default_type", "功能测试"),
            default_priority=gen.get("default_priority", "中"),
        )

        imp = data.get("import", {})
        import_cfg = ImportConfig(
            link_to_story=bool(imp.get("link_to_story", False)),
            dry_run=bool(imp.get("dry_run", False)),
            output_dir=imp.get("output_dir", "./output"),
        )

        llm_data = data.get("llm", {})
        llm = LLMConfig(
            api_key=os.getenv("OPENAI_API_KEY", llm_data.get("api_key")),
            base_url=os.getenv("OPENAI_BASE_URL", llm_data.get("base_url", "https://api.openai.com/v1")),
            model=os.getenv("OPENAI_MODEL", llm_data.get("model", "gpt-4o-mini")),
            temperature=float(llm_data.get("temperature", 0.3)),
        )

        return cls(tapd=tapd, story_filter=story_filter, generator=generator, import_=import_cfg, llm=llm)

    def validate(self) -> None:
        if not self.tapd.workspace_id:
            raise ValueError("缺少 TAPD_WORKSPACE_ID / tapd.workspace_id 配置")
        if not self.tapd.access_token and not (self.tapd.client_id and self.tapd.client_secret):
            raise ValueError("请配置 TAPD_ACCESS_TOKEN 或 TAPD_CLIENT_ID + TAPD_CLIENT_SECRET")
        if self.import_.link_to_story and not self.tapd.test_plan_id:
            raise ValueError("开启 link_to_story 时必须配置 TAPD_TEST_PLAN_ID")
        if self.generator.mode == "llm" and not self.llm.api_key:
            raise ValueError("LLM 模式需要配置 OPENAI_API_KEY")
