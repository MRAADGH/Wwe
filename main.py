import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# إعداد التسجيل المفصل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# رابط الموقع
WEBSITE_URL = "http://sip.vipcaller.net/mbilling/"

def setup_driver():
    """إعداد متصفح Chrome مع إعدادات محسنة"""
    options = Options()
    
    # إضافة وكيل مستخدم يبدو وكأنه حقيقي
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
    
    options.add_argument("--headless")  # إزالة هذا الخيار إذا كنت تريد مشاهدة المتصفح
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--dns-prefetch-disable")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # إعداد متغيرات البيئة للمسارات
    chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    chrome_driver_path = os.getenv("CHROME_DRIVER_PATH", "/usr/bin/chromedriver")
    
    options.binary_location = chrome_bin
    service = Service(executable_path=chrome_driver_path)
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver

def login(username, password):
    """محاولة تسجيل الدخول إلى الموقع"""
    driver = setup_driver()
    try:
        logger.info("فتح الموقع...")
        driver.get(WEBSITE_URL)
        
        # الانتظار حتى تحميل الصفحة بالكامل
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # العثور على حقل اسم المستخدم
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        username_field.clear()
        username_field.send_keys(username)
        
        # العثور على حقل كلمة المرور
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.clear()
        password_field.send_keys(password)
        
        # الضغط على زر تسجيل الدخول
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_button.click()

        # الانتظار حتى نجاح تسجيل الدخول
        try:
            dashboard = wait.until(EC.presence_of_element_located((By.ID, "dashboard")))
            logger.info("✅ تم تسجيل الدخول بنجاح!")
            return True
        except TimeoutException:
            logger.error("❌ فشل تسجيل الدخول. تأكد من صحة بيانات الدخول.")
            return False

    except Exception as e:
        logger.error(f"حدث خطأ: {str(e)}")
        return False

    finally:
        driver.quit()

if __name__ == "__main__":
    username = "أدخل_اسم_المستخدم"  # استبدل هذا باسم المستخدم الفعلي
    password = "أدخل_كلمة_المرور"  # استبدل هذا بكلمة المرور الفعلية
    if login(username, password):
        print("تم تسجيل الدخول بنجاح!")
    else:
        print("فشل تسجيل الدخول.")
