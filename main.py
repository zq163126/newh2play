import sys
import os
import requests
from playwright.sync_api import sync_playwright
from browser import BrowserManager 

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def send_telegram(message, photo_path=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': message})
    if photo_path and os.path.exists(photo_path):
        with open(photo_path, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", data={'chat_id': chat_id}, files={'photo': f})

def run_automation():
    page = None
    try:
        with sync_playwright() as p:
            with BrowserManager(p) as context:
                page = context.new_page()
                
                print("正在访问...")
                page.goto("https://host2play.gratis/server/renew?i=0b2f82c5-df07-4457-a2d9-9d948ce3d12d")
                page.wait_for_load_state("networkidle")
                
                # 步骤1：直接发送第一张截图
                page.screenshot(path="step1_load.png")
                send_telegram("页面已打开，当前状态：", "step1_load.png")
                
                # 步骤2：尝试点击
                print("准备点击 Renew server...")
                btn = page.get_by_role("button", name="Renew server")
                btn.wait_for(state="visible", timeout=30000)
                btn.click()
                
                # 步骤3：等待弹窗并截图
                print("已点击，等待弹窗...")
                page.wait_for_selector(".swal2-confirm", timeout=30000)
                page.screenshot(path="step2_popup.png")
                send_telegram("点击成功，弹窗已出现：", "step2_popup.png")
                
                page.get_by_role("button", name="Renew").click()
                send_telegram("Renew 操作成功完成！")
                
    except Exception as e:
        error_msg = f"Renew 报错: {str(e)}"
        print(error_msg)
        if page:
            page.screenshot(path="error.png")
            send_telegram(error_msg, "error.png")
        else:
            send_telegram(error_msg)

if __name__ == "__main__":
    run_automation()
