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

# 恢复为你确认有效的配置
MAGIC_URL = "https://nopecha.com/setup#_version=0|keys=|enabled=false|disabled_hosts=|input_method=auto|hook_method=auto|mouse_speed=medium|mouse_visualization=true|awscaptcha_auto_open=false|awscaptcha_auto_solve=false|awscaptcha_solve_delay_time=1000|awscaptcha_solve_delay=true|geetest_auto_open=false|geetest_auto_solve=false|geetest_solve_delay_time=1000|geetest_solve_delay=true|funcaptcha_auto_open=false|funcaptcha_auto_solve=false|funcaptcha_solve_delay_time=1000|funcaptcha_solve_delay=true|hcaptcha_auto_open=true|hcaptcha_auto_solve=true|hcaptcha_solve_delay_time=3000|hcaptcha_solve_delay=true|lemincaptcha_auto_open=false|lemincaptcha_auto_solve=false|lemincaptcha_solve_delay_time=1000|lemincaptcha_solve_delay=true|perimeterx_auto_solve=false|perimeterx_solve_delay_time=1000|perimeterx_solve_delay=true|recaptcha_auto_open=true|recaptcha_auto_solve=true|recaptcha_solve_delay_time=2000|recaptcha_solve_delay=true|textcaptcha_auto_solve=false|textcaptcha_image_selector=|textcaptcha_input_selector=|textcaptcha_math_expression=false|textcaptcha_solve_delay_time=100|textcaptcha_solve_delay=true|turnstile_auto_solve=true|turnstile_solve_delay_time=5000|turnstile_solve_delay=true"

class BrowserManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self.context: Optional[BrowserContext] = None

    def __enter__(self) -> BrowserContext:
        nopecha_enabled = os.getenv("NOPECHA_ENABLED", "true").lower() == "true"
        CHROME_PROFILE_DIR.mkdir(exist_ok=True)
        
        # 强制锁定代理端口到 10808，不再依赖不确定的环境变量
        proxy_url = "http://127.0.0.1:10808"
        proxy_config = {"server": proxy_url}

        launch_args = [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
        ]
        if nopecha_enabled:
            launch_args += [
                f"--disable-extensions-except={NOPECHA_EXTENSION_PATH}",
                f"--load-extension={NOPECHA_EXTENSION_PATH}",
            ]

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

        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = {runtime: {}};
        """)

        if nopecha_enabled:
            self._apply_magic_config()
            self._check_nopecha_status(proxy_url)

        return self.context

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass

    def _apply_magic_config(self):
        page = self.context.new_page()
        try:
            page.goto(MAGIC_URL, wait_until="load", timeout=15_000)
            page.wait_for_timeout(3000)
        finally:
            page.close()

    def _check_nopecha_status(self, proxy_url: str):
        # 明确指定代理，确保查询状态也走 10808 端口
        proxies = {"http": proxy_url, "https": proxy_url}
        try:
            response = requests.get("https://api.nopecha.com/v1/status", proxies=proxies, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"--- NopeCHA 状态正常: 剩余额度={data.get('credit')} ---")
        except Exception as e:
            print(f"--- NopeCHA 额度查询失败: {e} ---")
