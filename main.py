
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توكن البوت
TOKEN = "7852676274:AAHIx3Q9qFbylmvHKDhbhT5nEpFOFA5i2CM"

# حالات المحادثة
USERNAME, PASSWORD, CALLER_ID = range(3)

# رابط الموقع
WEBSITE_URL = "http://sip.vipcaller.net/mbilling/"

# تحديد مسارات Chrome
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium")
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER", "/usr/bin/chromedriver")

# تخزين جلسة المتصفح
driver = None

def setup_chrome_options():
    """إعداد خيارات متصفح كروم"""
    options = Options()
    options.binary_location = CHROME_BIN
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return options

def create_driver():
    """إنشاء متصفح جديد"""
    global driver
    if driver:
        try:
            driver.quit()
        except:
            pass
    options = setup_chrome_options()
    service = Service(executable_path=CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر البداية"""
    keyboard = [[InlineKeyboardButton("تسجيل الدخول", callback_data='login')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'مرحباً بك في بوت خدمة تغيير معرف المتصل\nاضغط على زر تسجيل الدخول للبدء',
        reply_markup=reply_markup
    )

async def login_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج زر تسجيل الدخول"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔐 تسجيل الدخول\n\nالرجاء إدخال اسم المستخدم:"
    )
    return USERNAME

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج استلام اسم المستخدم"""
    context.user_data['username'] = update.message.text
    await update.message.reply_text("🔑 الرجاء إدخال كلمة المرور:")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج استلام كلمة المرور ومحاولة تسجيل الدخول"""
    try:
        username = context.user_data.get('username')
        password = update.message.text
        
        if not username:
            await update.message.reply_text("❌ حدث خطأ: لم يتم العثور على اسم المستخدم. الرجاء البدء من جديد باستخدام /start")
            return ConversationHandler.END
        
        # إنشاء جلسة جديدة للمتصفح
        driver = create_driver()
        logger.info("تم إنشاء المتصفح بنجاح")
        
        # فتح صفحة تسجيل الدخول
        driver.get(WEBSITE_URL)
        logger.info("تم فتح صفحة تسجيل الدخول")
        
        # إنشاء كائن WebDriverWait
        wait = WebDriverWait(driver, 30)
        
        # انتظار وإدخال اسم المستخدم
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        logger.info("تم العثور على حقل اسم المستخدم")
        username_field.clear()
        username_field.send_keys(username)
        
        # إدخال كلمة المرور
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(password)
        logger.info("تم إدخال بيانات تسجيل الدخول")
        
        # الضغط على زر تسجيل الدخول
        login_button = driver.find_element(By.ID, "login-button")
        login_button.click()
        logger.info("تم الضغط على زر تسجيل الدخول")
        
        # التحقق من نجاح تسجيل الدخول
        try:
            # انتظار ظهور لوحة التحكم
            dashboard = wait.until(
                EC.presence_of_element_located((By.ID, "dashboard"))
            )
            logger.info("تم تسجيل الدخول بنجاح")
            await update.message.reply_text(
                "✅ تم تسجيل الدخول بنجاح!\n\n"
                "الرجاء إدخال معرف المتصل الجديد:"
            )
            return CALLER_ID
        except TimeoutException:
            logger.error("فشل تسجيل الدخول - لم يتم العثور على لوحة التحكم")
            await update.message.reply_text(
                "❌ فشل تسجيل الدخول\n"
                "تأكد من صحة اسم المستخدم وكلمة المرور"
            )
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {str(e)}")
        await update.message.reply_text(
            "❌ حدث خطأ غير متوقع\n"
            "الرجاء المحاولة مرة أخرى لاحقاً"
        )
        return ConversationHandler.END
    
    finally:
        if driver:
            driver.quit()
            logger.info("تم إغلاق المتصفح")

async def change_caller_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج تغيير معرف المتصل"""
    try:
        new_caller_id = update.message.text
        driver = create_driver()
        wait = WebDriverWait(driver, 30)
        
        # البحث عن حقل معرف المتصل
        caller_id_field = wait.until(
            EC.element_to_be_clickable((By.ID, "caller-id"))
        )
        caller_id_field.clear()
        caller_id_field.send_keys(new_caller_id)
        
        # حفظ التغييرات
        save_button = wait.until(
            EC.element_to_be_clickable((By.ID, "save-button"))
        )
        save_button.click()
        
        # التحقق من نجاح العملية
        success_message = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )
        
        await update.message.reply_text(
            f"✅ تم تغيير معرف المتصل بنجاح إلى: {new_caller_id}"
        )
        
    except Exception as e:
        logger.error(f"خطأ في تغيير معرف المتصل: {str(e)}")
        await update.message.reply_text(
            "❌ حدث خطأ أثناء تغيير معرف المتصل\n"
            "الرجاء المحاولة مرة أخرى"
        )
    
    finally:
        if driver:
            driver.quit()
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج إلغاء العملية"""
    await update.message.reply_text('تم إلغاء العملية')
    return ConversationHandler.END

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    # إنشاء تطبيق البوت
    application = Application.builder().token(TOKEN).build()
    
    # إعداد معالج المحادثة
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(login_button, pattern='^login$')
        ],
        states={
            USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)
            ],
            PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)
            ],
            CALLER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, change_caller_id)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=True
    )
    
    # إضافة المعالج
    application.add_handler(conv_handler)
    
    # تشغيل البوت
    application.run_polling()

if __name__ == '__main__':
    main()
