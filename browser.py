import os
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from patchright.sync_api import BrowserContext, Playwright

load_dotenv()

BASE_DIR = Path(__file__).parent.absolute()
NOPECHA_EXTENSION_PATH = BASE_DIR / "extensions" / "nopecha"
CHROME_PROFILE_DIR = BASE_DIR / ".chrome_profile"

# 使用你当前确认有效的 Magic URL
MAGIC_URL = "https://nopecha.com/setup#_version=0|keys=|enabled=true|recaptcha_auto_open=true|recaptcha_auto_solve=true|recaptcha_solve_delay_time=5000|hcaptcha_auto_open=true|hcaptcha_auto_solve=true|hcaptcha_solve_delay_time=5000|mouse_speed=slow"

class BrowserManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self.context: Optional[BrowserContext] = None

    def __enter__(self) -> BrowserContext:
        nopecha_enabled = os.getenv("NOPECHA_ENABLED", "true").lower() == "true"
        CHROME_PROFILE_DIR.mkdir(exist_ok=True)

        launch_args = [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
        ]
        if nopecha_enabled:
            launch_args += [
                f"--disable-extensions-except={NOPECHA_EXTENSION_PATH}",
                f"--load-extension={NOPECHA_EXTENSION_PATH}",
            ]

        proxy_url = "http://127.0.0.1:10808"
        proxy_config = {"server": proxy_url}

        # --- 完全照搬旧版 context 创建逻辑 ---
        self.context = self.playwright.chromium.launch_persistent_context(
            str(CHROME_PROFILE_DIR),
            channel="chromium",
            headless=False,
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            args=launch_args,
            env={**os.environ},
            proxy=proxy_config,
        )

        # --- 完全照搬旧版欺骗注入 ---
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = {runtime: {}};
        """)

        # --- 完全照搬旧版初始化流程 ---
        if nopecha_enabled:
            self._apply_magic_config()
            self._check_nopecha_status(proxy_url)

        return self.context

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass

    # --- 完全照搬旧版注入流程 ---
    def _apply_magic_config(self):
        page = self.context.new_page()
        try:
            page.goto(MAGIC_URL, wait_until="load", timeout=10_000)
            page.wait_for_timeout(2000)
        finally:
            page.close()

    def _check_nopecha_status(self, proxy_url: str):
        proxies = {"http": proxy_url, "https": proxy_url}
        try:
            response = requests.get("https://api.nopecha.com/v1/status", proxies=proxies, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"--- NopeCHA 状态正常: 剩余额度={data.get('credit')} ---")
        except:
            pass
