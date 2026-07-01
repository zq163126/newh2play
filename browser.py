import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from patchright.sync_api import BrowserContext, Playwright

load_dotenv()

BASE_DIR = Path(__file__).parent.absolute()
NOPECHA_EXTENSION_PATH = BASE_DIR / "extensions" / "nopecha"
CHROME_PROFILE_DIR = BASE_DIR / ".chrome_profile"

# Magic URL 依然是配置的核心
MAGIC_URL = "https://nopecha.com/setup#_version=0|keys=|enabled=false|disabled_hosts=|input_method=auto|hook_method=auto|mouse_speed=medium|mouse_visualization=true|awscaptcha_auto_open=false|awscaptcha_auto_solve=false|awscaptcha_solve_delay_time=1000|awscaptcha_solve_delay=true|geetest_auto_open=false|geetest_auto_solve=false|geetest_solve_delay_time=1000|geetest_solve_delay=true|funcaptcha_auto_open=false|funcaptcha_auto_solve=false|funcaptcha_solve_delay_time=1000|funcaptcha_solve_delay=true|hcaptcha_auto_open=true|hcaptcha_auto_solve=true|hcaptcha_solve_delay_time=3000|hcaptcha_solve_delay=true|lemincaptcha_auto_open=false|lemincaptcha_auto_solve=false|lemincaptcha_solve_delay_time=1000|lemincaptcha_solve_delay=true|perimeterx_auto_solve=false|perimeterx_solve_delay_time=1000|perimeterx_solve_delay=true|recaptcha_auto_open=true|recaptcha_auto_solve=true|recaptcha_solve_delay_time=2000|recaptcha_solve_delay=true|textcaptcha_auto_solve=false|textcaptcha_image_selector=|textcaptcha_input_selector=|textcaptcha_math_expression=false|textcaptcha_solve_delay_time=100|textcaptcha_solve_delay=true|turnstile_auto_solve=true|turnstile_solve_delay_time=5000|turnstile_solve_delay=true"

class BrowserManager:
    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        self.context: Optional[BrowserContext] = None

    def __enter__(self) -> BrowserContext:
        CHROME_PROFILE_DIR.mkdir(exist_ok=True)
        
        # 强制使用本地 gost 代理
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

        # 仅注入配置，不查状态，彻底规避 403 干扰
        self._apply_magic_config()
        
        return self.context

    def _apply_magic_config(self):
        page = self.context.new_page()
        try:
            print("正在注入配置...")
            page.goto(MAGIC_URL, wait_until="networkidle", timeout=20_000)
            page.wait_for_timeout(3000)
            print("配置注入完毕。")
        except Exception as e:
            print(f"注入配置时网络异常: {e}")
        finally:
            page.close()

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass
