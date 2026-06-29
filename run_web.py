#!/usr/bin/env python3
"""启动 TAPD 测试用例生成 Web 页面。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from web.app import app  # noqa: E402

if __name__ == "__main__":
    print("TAPD 测试用例生成器已启动: http://127.0.0.1:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)
