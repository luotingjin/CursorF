#!/usr/bin/env python3
"""启动 TAPD 测试用例生成 Web 页面。"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

env_file = ROOT / ".env"
load_dotenv(env_file, override=True)

from web.app import app  # noqa: E402

if __name__ == "__main__":
    client_id = os.getenv("TAPD_CLIENT_ID", "")
    has_secret = bool(os.getenv("TAPD_CLIENT_SECRET", "").strip())
    print(f"TAPD 测试用例生成器已启动: http://127.0.0.1:8080")
    print(f"配置文件: {env_file} ({'已加载' if env_file.exists() else '未找到'})")
    print(f"TAPD_CLIENT_ID: {client_id or '(未配置)'}")
    print(f"TAPD_CLIENT_SECRET: {'已配置' if has_secret else '(未配置)'}")
    app.run(host="0.0.0.0", port=8080, debug=False)
