import os
import time
import requests
from playwright.sync_api import sync_playwright
from browser import BrowserManager 

def send_telegram(message, photo_path=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': message})
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", data={'chat_id': chat_id}, files={'photo': f})
    except Exception as e:
        print(f"Telegram 发送失败: {e}")

def run_automation():
    page = None
    try:
        with sync_playwright() as p:
            with BrowserManager(p) as context:
                page = context.new_page()
                page.set_viewport_size({"width": 1280, "height": 720})
                
                print("访问目标页面...")
                page.goto("https://host2play.gratis/server/renew?i=0b2f82c5-df07-4457-a2d9-9d948ce3d12d")
                time.sleep(5)

                # 1. 暴力清理阻碍元素（移植自成功的 DrissionPage 逻辑）
                print("清理阻碍元素...")
                page.evaluate("""() => {
                    const selectors = ['ins.adsbygoogle', 'iframe[src*="ads"]', '.modal-backdrop', '[id*="consent"]', '[class*="consent"]', '.loading-spinner'];
                    selectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    });
                }""")
                
                print("等待 Renew 卡片显示...")
                page.wait_for_selector("#renew", state="visible", timeout=30000)
                
                print("点击 Renew server...")
                # 使用 force=True 确保点击不受遮罩影响
                page.get_by_role("button", name="Renew server").click(force=True)
                
                # 2. 验证码检测与激活逻辑
                time.sleep(3)
                # 使用 locator 查找 iframe 元素，它具有 count() 方法
                captcha_frame = page.locator("iframe[src*='recaptcha/api2/bframe']")
                
                if captcha_frame.count() > 0:
                    print("检测到验证码，准备激活...")
                    try:
                        # 尝试通过点击 anchor 触发验证码插件
                        page.locator("iframe[src*='recaptcha/api2/anchor']").content_frame.get_by_role("checkbox").click()
                    except Exception as e:
                        print(f"激活验证码失败: {e}")
                    
                    print("等待 NopeCHA 处理 (40秒)...")
                    time.sleep(40) 
                
                print("执行最终确认...")
                # 尝试点击最终的 Renew 按钮
                try:
                    page.get_by_role("button", name="Renew").click(force=True)
                except Exception as e:
                    print(f"最终确认失败: {e}")

                time.sleep(5)
                page.screenshot(path="final.png", full_page=True)
                send_telegram("流程结束，查看截图确认结果。", "final.png")
                
    except Exception as e:
        error_msg = f"任务执行出错: {str(e)}"
        print(error_msg)
        if page:
            page.screenshot(path="error.png", full_page=True)
            send_telegram(error_msg, "error.png")
        else:
            send_telegram(error_msg)

if __name__ == "__main__":
    run_automation()
