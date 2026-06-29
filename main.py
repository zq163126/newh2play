import sys
import os
import requests
# 强制将当前脚本路径加入搜索路径，解决 ImportError 问题
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
# 导入你原来的浏览器管理器
from browser import BrowserManager 

def send_telegram(message, photo_path=None):
    """发送通知到 Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram 环境变量缺失，无法发送通知")
        return
    
    # 发送文本
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  data={'chat_id': chat_id, 'text': message})
    
    # 发送截图
    if photo_path and os.path.exists(photo_path):
        with open(photo_path, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                          data={'chat_id': chat_id}, files={'photo': f})

def run_automation():
    try:
        with sync_playwright() as p:
            # 使用你原始的 browser.py 中的 BrowserManager
            with BrowserManager(p) as context:
                page = context.new_page()
                
                # 去广告：拦截器
                def block_ads(route):
                    if any(ad in route.request.url for ad in ["doubleclick.net", "google-analytics.com", "adservice"]):
                        route.abort()
                    else:
                        route.continue_()
                page.route("**/*", block_ads)
                
                # 1. 访问目标
                print("正在访问目标页面...")
                page.goto("https://host2play.gratis/server/renew?i=0b2f82c5-df07-4457-a2d9-9d948ce3d12d")
                
                # 2. 点击 Renew server (鲁棒定位)
                print("点击 Renew server...")
                page.get_by_role("button", name="Renew server").click()
                
                # 3. 处理人机验证并确认
                # 等待 swal2 弹窗出现
                print("等待验证及确认弹窗...")
                page.wait_for_selector(".swal2-confirm", timeout=60000)
                
                # 点击弹窗里的确认 Renew 按钮
                page.get_by_role("button", name="Renew").click()
                
                # 4. 截图并通知
                screenshot_path = "result.png"
                page.screenshot(path=screenshot_path)
                send_telegram("Renew 操作成功完成！", screenshot_path)
                print("任务完成，已发送 Telegram 通知")
                
    except Exception as e:
        error_msg = f"Renew 任务执行失败: {str(e)}"
        print(error_msg)
        send_telegram(error_msg)

if __name__ == "__main__":
    run_automation()
