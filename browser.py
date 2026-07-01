import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from patchright.sync_api import BrowserContext, Playwright

load_dotenv()

BASE_DIR = Path(__file__).parent.absolute()
NOPECHA_EXTENSION_PATH = BASE_DIR / "extensions" / "nopecha"
CHROME_PROFILE_DIR = BASE_DIR / ".chrome_profile"

# 优化后的配置：增加延迟，让插件有足够时间完成服务器通信
MAGIC_URL = "https://nopecha.com/setup#_version=0|keys=|enabled=true|recaptcha_auto_open=true|recaptcha_auto_solve=true|recaptcha_solve_delay_time=5000|hcaptcha_auto_open=true|hcaptcha_auto_solve=true|hcaptcha_solve_delay_time=5000|mouse_speed=slow"

class BrowserManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self.context: Optional[BrowserContext] = None

    def __enter__(self) -> BrowserContext:
        CHROME_PROFILE_DIR.mkdir(exist_ok=True)
        proxy_url = "http://127.0.0.1:10808"
        
        launch_args = [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            f"--load-extension={NOPECHA_EXTENSION_PATH}",
            f"--disable-extensions-except={NOPECHA_EXTENSION_PATH}",
            f"--proxy-server={proxy_url}"
        ]
        
        self.context = self.playwright.chromium.launch_persistent_context(
            str(CHROME_PROFILE_DIR),
            channel="chromium",
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=launch_args,
        )

        # 注入防检测脚本
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = {runtime: {}};
        """)

        # 注入配置
        self._apply_magic_config()
        
        return self.context

    def _apply_magic_config(self):
        page = self.context.new_page()
        try:
            page.goto(MAGIC_URL, wait_until="load", timeout=20_000)
            page.wait_for_timeout(3000)
        finally:
            page.close()

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass
