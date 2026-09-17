"""
Launcher script for TypeSafe Tetris Ultra-Crisp Web Dashboard.
Supports both standalone repo execution and module package execution:
    python main.py
    python web_launcher.py
    python -m tetris.main
"""

import os
import sys
import time
import threading
import webbrowser
import uvicorn

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(1, PARENT_DIR)

try:
    from tetris.web.server import app
except ImportError:
    from web.server import app


def open_browser(url: str):
    """延迟 1 秒等待服务器启动后自动打开系统默认浏览器"""
    time.sleep(1.0)
    try:
        webbrowser.open(url)
    except Exception:
        pass



def main(host: str = "127.0.0.1", port: int = 8000, auto_open: bool = True):
    url = f"http://{host}:{port}"
    if auto_open:
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
