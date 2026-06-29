import os
import requests
from playwright.sync_api import sync_playwright
from browser_manager import BrowserManager

def block_ads(route):
    if any(p in route.request.url for p in ["doubleclick.net", "google-analytics.com"]):
        route.abort()
    else:
        route.continue_()

def run():
    with sync_playwright() as p:
        with BrowserManager(p) as context:
            page = context.new_page()
            page.route("**/*", block_ads)
            
            # 1. 访问页面
            page.goto("https://host2play.gratis/server/renew?i=0b2f82c5-df07-4457-a2d9-9d948ce3d12d")
            
            # 2. 点击 Renew server (鲁棒定位)
            page.get_by_role("button", name="Renew server").click()
            
            # 3. 等待验证并 Renew
            page.wait_for_selector(".swal2-confirm", timeout=60000)
            page.get_by_role("button", name="Renew").click()
            
            # 4. 截图并通知
            page.screenshot(path="result.png")
            
            # 发送 Telegram
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                          data={'chat_id': chat_id}, files={'photo': open('result.png', 'rb')})

if __name__ == "__main__":
    run()
