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

                page.evaluate("""() => {
                    const selectors = ['ins.adsbygoogle', 'iframe[src*="ads"]', '.modal-backdrop', '[id*="consent"]', '[class*="consent"]', '.loading-spinner'];
                    selectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    });
                }""")
                
                print("点击 Renew server...")
                page.wait_for_selector("#renew", state="visible", timeout=30000)
                page.get_by_role("button", name="Renew server").click(force=True)
                
                time.sleep(3)
                if page.locator("iframe[src*='recaptcha/api2/bframe']").count() > 0:
                    print("检测到验证码，准备激活...")
                    try:
                        page.locator("iframe[src*='recaptcha/api2/anchor']").content_frame.get_by_role("checkbox").click()
                    except: pass
                    
                    print("开始实时监控验证过程...")
                    for i in range(9): # 总共 90 秒监控
                        time.sleep(10)
                        # 实时截屏并发送
                        screenshot_name = f"monitor_{i}.png"
                        page.screenshot(path=screenshot_name, full_page=True)
                        send_telegram(f"验证码处理中... ({ (i+1)*10 }秒)", screenshot_name)
                        
                        # 检查验证码是否消失
                        if page.locator("iframe[src*='recaptcha/api2/bframe']").count() == 0:
                            print("✅ 验证码已通过！")
                            break
                
                print("执行最终确认...")
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
