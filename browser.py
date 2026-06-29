import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from patchright.sync_api import BrowserContext, Playwright

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

BASE_DIR = Path(__file__).parent.absolute()
NOPECHA_EXTENSION_PATH = BASE_DIR / "extensions" / "nopecha"
CHROME_PROFILE_DIR = BASE_DIR / ".chrome_profile"

class BrowserManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self._display = None
        self.context: Optional[BrowserContext] = None

    def __enter__(self) -> BrowserContext:
        # 严格按照之前成功时的逻辑启动 Xvfb
        from xvfbwrapper import Xvfb
        self._display = Xvfb(width=1920, height=1080)
        self._display.start()
        
        # 显式重置 DISPLAY 环境变量
        os.environ["DISPLAY"] = f":{self._display.new_display}"

        CHROME_PROFILE_DIR.mkdir(exist_ok=True)

        # 这里保持最基础的参数，先确保能打开网页，排除插件干扰
        launch_args = [
            "--no-sandbox",
            "--ozone-platform=x11",
            f"--load-extension={NOPECHA_EXTENSION_PATH}",
            f"--disable-extensions-except={NOPECHA_EXTENSION_PATH}",
        ]

        # 显式传入 child_env，确保浏览器进程能读取到刚才设置的 DISPLAY
        child_env = {**os.environ}

        self.context = self.playwright.chromium.launch_persistent_context(
            str(CHROME_PROFILE_DIR),
            channel="chromium",
            headless=False,
            viewport={"width": 1920, "height": 1080},
            args=launch_args,
            env=child_env,
        )
        return self.context

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass
        if self._display:
            try: self._display.stop()
            except: pass
