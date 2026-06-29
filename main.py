import sys
import os
import requests
from playwright.sync_api import sync_playwright
from browser import BrowserManager 

# 确保能找到同目录文件
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
                print("正在访问目标页面...")
                page.goto("https://host2play.gratis/server/renew?i=0b2f82c5-df07-4457-a2d9-9d948ce3d12d")
                
                # --- 截图排查遮挡 ---
                page.wait_for_load_state("networkidle")
                page.screenshot(path="debug_before_click.png")
                print("已截图，请检查 Artifacts 中的 debug_before_click.png")
                # ------------------
                
                # 继续执行你的原逻辑
                print("点击 Renew server...")
                btn = page.get_by_role("button", name="Renew server")
                btn.wait_for(state="visible", timeout=30000)
                btn.click()
                
                print("等待弹窗...")
                page.wait_for_selector(".swal2-confirm", timeout=30000)
                page.get_by_role("button", name="Renew").click()
                
                page.screenshot(path="result.png")
                send_telegram("Renew 操作成功！", "result.png")
                
    except Exception as e:
        error_msg = f"Renew 任务执行失败: {str(e)}"
        print(error_msg)
        if page:
            page.screenshot(path="error_screenshot.png")
            send_telegram(error_msg, "error_screenshot.png")
        else:
            send_telegram(error_msg)

if __name__ == "__main__":
    run_automation()
