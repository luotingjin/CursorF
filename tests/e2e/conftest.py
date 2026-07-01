"""Playwright E2E 测试：自动启动 Flask 测试服务器。"""

from __future__ import annotations

import socket
import threading

import pytest
from werkzeug.serving import make_server

from web.app import app


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def base_url() -> str:
    port = _find_free_port()
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict) -> dict:
    # 优先使用本机 Chrome，避免 playwright install 下载失败
    return {**browser_type_launch_args, "channel": "chrome"}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    return {**browser_context_args, "locale": "zh-CN"}
