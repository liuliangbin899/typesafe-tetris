"""
Main Application Entrypoint for TypeSafe Tetris.
Pure Headless Engine + High-Definition Web Cockpit powered by FastAPI & WebSockets.

Supports both:
  1. Standalone execution: `python main.py`
  2. Package execution:    `python -m tetris.main`
"""

import os
import sys
import argparse

# 兼容独立运行与包内运行路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(1, PARENT_DIR)

try:
    from tetris.web_launcher import main as run_web_cockpit
except ImportError:
    from web_launcher import main as run_web_cockpit


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TypeSafe Tetris Ultra-Crisp Web Dashboard",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Web 服务器监听端口",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Web 服务器绑定地址",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="禁止启动时自动唤起系统浏览器",
    )

    args = parser.parse_args()

    run_web_cockpit(
        host=args.host,
        port=args.port,
        auto_open=not args.no_browser,
    )


if __name__ == "__main__":
    main()
