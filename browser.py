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

# 优化配置：增加延迟以匹配云端服务器响应速度
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
            env={**os.environ} # 确保读取环境变量
        )

        # 1. 注入防检测脚本
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = {runtime: {}};
        """)

        # 2. 注入插件配置
        self._apply_magic_config()
        
        # 3. 监控额度状态
        self._log_nopecha_credit()
        
        return self.context

    def _apply_magic_config(self):
        page = self.context.new_page()
        try:
            page.goto(MAGIC_URL, wait_until="load", timeout=20_000)
            page.wait_for_timeout(3000)
        finally:
            page.close()

    def _log_nopecha_credit(self):
        """记录额度信息，便于在日志中观察消耗"""
        print("\n--- [NopeCHA] 当前 API 账户状态 ---")
        try:
            # 这里的请求如果还是 403，会直接在 except 中捕获，不会影响浏览器运行
            response = requests.get("https://api.nopecha.com/v1/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"状态: {data.get('status')} | 剩余额度: {data.get('credit')}")
            else:
                print(f"API 状态获取受限 (Code: {response.status_code})，请观察网页插件交互。")
        except Exception as e:
            print(f"API 状态检查异常: {e} (这不影响插件在网页端正常工作)")
        print("----------------------------------\n")

    def __exit__(self, *_):
        if self.context:
            try: self.context.close()
            except: pass
