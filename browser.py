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

# Magic URL 必须作为第一优先级
MAGIC_URL = "https://nopecha.com/setup#_version=0|keys=|enabled=false|disabled_hosts=|input_method=auto|hook_method=auto|mouse_speed=medium|mouse_visualization=true|awscaptcha_auto_open=false|awscaptcha_auto_solve=false|awscaptcha_solve_delay_time=1000|awscaptcha_solve_delay=true|geetest_auto_open=false|geetest_auto_solve=false|geetest_solve_delay_time=1000|geetest_solve_delay=true|funcaptcha_auto_open=false|funcaptcha_auto_solve=false|funcaptcha_solve_delay_time=1000|funcaptcha_solve_delay=true|hcaptcha_auto_open=true|hcaptcha_auto_solve=true|hcaptcha_solve_delay_time=3000|hcaptcha_solve_delay=true|lemincaptcha_auto_open=false|lemincaptcha_auto_solve=false|lemincaptcha_solve_delay_time=1000|lemincaptcha_solve_delay=true|perimeterx_auto_solve=false|perimeterx_solve_delay_time=1000|perimeterx_solve_delay=true|recaptcha_auto_open=true|recaptcha_auto_solve=true|recaptcha_solve_delay_time=2000|recaptcha_solve_delay=true|textcaptcha_auto_solve=false|textcaptcha_image_selector=|textcaptcha_input_selector=|textcaptcha_math_expression=false|textcaptcha_solve_delay_time=100|textcaptcha_solve_delay=true|turnstile_auto_solve=true|turnstile_solve_delay_time=5000|turnstile_solve_delay=true"

class BrowserManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self.context: Optional[BrowserContext] = None

    def __enter__(self) -> BrowserContext:
        nopecha_enabled = os.getenv("NOPECHA_ENABLED", "true").lower() == "true"
        CHROME_PROFILE_DIR.mkdir(exist_ok=True)

        launch_args = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        if nopecha_enabled:
            launch_args += [
                f"--disable-extensions-except={NOPECHA_EXTENSION_PATH}",
                f"--load-extension={NOPECHA_EXTENSION_PATH}",
            ]

        proxy_url = os.getenv("PROXY_SOCKS5")
        proxy_config = {"server": proxy_url} if proxy_url else None

        self.context = self.playwright.chromium.launch_persistent_context(
            str(CHROME_PROFILE_DIR),
            channel="chromium",
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=launch_args,
            proxy=proxy_config,
        )

        # 核心顺序：先注入 Magic URL，确保插件配置就位
        if nopecha_enabled:
            self._apply_magic_config()
            # 配置成功后再尝试查状态（如果此时还 403，那就彻底忽略状态检查）
            self._check_nopecha_status()

        return self.context

    def _apply_magic_config(self):
        print("正在应用 Magic URL 配置...")
        page = self.context.new_page()
        try:
            page.goto(MAGIC_URL, wait_until="networkidle", timeout=15_000)
            page.wait_for_timeout(3000)
        finally:
            page.close()

    def _check_nopecha_status(self):
        # 移除了 403 报错的干扰，如果不行就直接捕获异常不打印
        try:
            response = requests.get("https://api.nopecha.com/v1/status", timeout=3)
            if response.status_code == 200:
                print("NopeCHA 服务状态正常")
        except:
            pass 

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass
