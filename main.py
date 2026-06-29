import sys
import os
import requests
import time
from playwright.sync_api import sync_playwright
from browser import BrowserManager 

# 添加路径，确保能找到同目录文件
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
    try:
        with sync_playwright() as p:
            with BrowserManager(p) as context:
                page = context.new_page()
                
                # 1. 访问目标
                print("正在访问目标页面...")
                page.goto("https://host2play.gratis/server/renew?i=0b2f82c5-df07-4457-a2d9-9d948ce3d12d")
                
                # --- 排查步骤：截图页面初始状态 ---
                page.wait_for_load_state("networkidle") # 等待网络空闲
                page.screenshot(path="debug_page_load.png")
                print("已截取页面加载完成后的状态：debug_page_load.png")
                # ------------------------------

                # 2. 点击 Renew server
                # 增加更长的等待时间，并尝试匹配更广泛的定位符
                print("等待并点击 Renew server...")
                # 尝试点击，如果 get_by_role 找不到，可以使用 CSS 选择器作为备份
                btn = page.get_by_role("button", name="Renew server")
                
                # 确保按钮可见并可点击
                btn.wait_for(state="visible", timeout=30000)
                btn.click()
                
                # 3. 处理弹窗
                page.wait_for_selector(".swal2-confirm", timeout=30000)
                page.get_by_role("button", name="Renew").click()
                
                # 4. 成功截图
                page.screenshot(path="result.png")
                send_telegram("Renew 操作成功！", "result.png")
                
    except Exception as e:
        # --- 错误发生时立刻截图 ---
        error_screenshot = "error_screenshot.png"
        if 'page' in locals():
            page.screenshot(path=error_screenshot)
            send_telegram(f"Renew 失败，已截图: {str(e)}", error_screenshot)
        else:
            send_telegram(f"Renew 失败: {str(e)}")
        print(f"任务执行失败: {str(e)}")

if __name__ == "__main__":
    run_automation()
