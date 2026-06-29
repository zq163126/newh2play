import os
import requests
from playwright.sync_api import sync_playwright
from browser_manager import BrowserManager

# Telegram 通知函数
def send_telegram_msg(message, image_path=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    
    # 发送文本
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  data={'chat_id': chat_id, 'text': message})
    
    # 发送截图
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as photo:
            requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                          data={'chat_id': chat_id}, files={'photo': photo})

def run_renew_task():
    with sync_playwright() as p:
        # 启动你强大的浏览器环境
        with BrowserManager(p) as context:
            page = context.new_page()
            
            # 去广告逻辑：拦截常见广告域名
            def block_ads(route):
                if any(ad in route.request.url for ad in ["doubleclick.net", "google-analytics.com", "adservice"]):
                    route.abort()
                else:
                    route.continue_()
            page.route("**/*", block_ads)
            
            # 1. 访问目标页面
            page.goto("https://host2play.gratis/server/renew?i=0b2f82c5-df07-4457-a2d9-9d948ce3d12d")
            
            # 2. 点击 Renew server (鲁棒定位)
            # 使用 get_by_role 比 XPath 更稳定，能自动处理按钮点击
            page.get_by_role("button", name="Renew server").click()
            
            # 3. 等待弹窗并点击确认
            # 使用 wait_for_selector 等待 swal2 弹窗出现
            page.wait_for_selector(".swal2-confirm", timeout=60000)
            page.get_by_role("button", name="Renew").click()
            
            # 4. 截图保存结果
            page.screenshot(path="result.png")
            
            # 5. 发送结果到 Telegram
            send_telegram_msg("Renew 操作已执行，请查看截图。", "result.png")
            print("任务执行成功")

if __name__ == "__main__":
    run_renew_task()
