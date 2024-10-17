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
import traceback

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# التوكن
TOKEN = "7852676274:AAHIx3Q9qFbylmvHKDhbhT5nEpFOFA5i2CM"

# حالات المحادثة
CHOOSING_ACTION, USERNAME, PASSWORD, CALLER_ID = range(4)

# رابط الموقع
WEBSITE_URL = "http://sip.vipcaller.net/mbilling/"

def setup_driver():
    """إعداد متصفح Chrome"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # استخدام المسار المحدد في متغيرات البيئة
    chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    chrome_driver_path = os.getenv("CHROME_DRIVER_PATH", "/usr/bin/chromedriver")
    
    options.binary_location = chrome_bin
    service = Service(executable_path=chrome_driver_path)
    
    return webdriver.Chrome(service=service, options=options)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية المحادثة"""
    keyboard = [[InlineKeyboardButton("تسجيل الدخول", callback_data='login')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'مرحباً بك في بوت تغيير معرف المتصل\nاضغط على زر تسجيل الدخول للبدء',
        reply_markup=reply_markup
    )
    return CHOOSING_ACTION

async def login_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة نقر زر تسجيل الدخول"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إدخال اسم المستخدم:")
    return USERNAME

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة إدخال اسم المستخدم"""
    context.user_data['username'] = update.message.text
    await update.message.reply_text("الرجاء إدخال كلمة المرور:")
    return PASSWORD

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة إدخال كلمة المرور"""
    try:
        username = context.user_data.get('username')
        password = update.message.text

        status_message = await update.message.reply_text("جاري تسجيل الدخول...")

        driver = setup_driver()
        try:
            driver.get(WEBSITE_URL)
            wait = WebDriverWait(driver, 20)

            # إدخال اسم المستخدم وكلمة المرور
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.clear()
            username_field.send_keys(username)

            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)

            # الضغط على زر تسجيل الدخول
            login_button = driver.find_element(By.ID, "login-button")
            login_button.click()

            # التحقق من نجاح تسجيل الدخول
            try:
                wait.until(EC.presence_of_element_located((By.ID, "dashboard")))
                await status_message.edit_text("✅ تم تسجيل الدخول بنجاح!\nالرجاء إدخال معرف المتصل الجديد:")
                context.user_data['logged_in'] = True
                return CALLER_ID
            except TimeoutException:
                await status_message.edit_text("❌ فشل تسجيل الدخول\nالرجاء التأكد من صحة اسم المستخدم وكلمة المرور")
                return ConversationHandler.END

        finally:
            driver.quit()

    except Exception as e:
        logger.error(f"خطأ في تسجيل الدخول: {str(e)}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("❌ حدث خطأ أثناء محاولة تسجيل الدخول\nالرجاء المحاولة مرة أخرى")
        return ConversationHandler.END

async def handle_caller_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة تغيير معرف المتصل"""
    if not context.user_data.get('logged_in'):
        await update.message.reply_text("الرجاء تسجيل الدخول أولاً")
        return ConversationHandler.END

    status_message = await update.message.reply_text("جاري تغيير معرف المتصل...")
    new_caller_id = update.message.text
    
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 20)

        # تنفيذ تغيير معرف المتصل
        driver.get(WEBSITE_URL)
        caller_id_field = wait.until(EC.presence_of_element_located((By.ID, "caller-id")))
        caller_id_field.clear()
        caller_id_field.send_keys(new_caller_id)

        save_button = wait.until(EC.element_to_be_clickable((By.ID, "save-button")))
        save_button.click()

        await status_message.edit_text(f"✅ تم تغيير معرف المتصل بنجاح إلى: {new_caller_id}")
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"خطأ في تغيير معرف المتصل: {str(e)}")
        await status_message.edit_text("❌ حدث خطأ أثناء تغيير معرف المتصل")
        return ConversationHandler.END

    finally:
        if driver:
            driver.quit()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء العملية"""
    await update.message.reply_text('تم إلغاء العملية')
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الأخطاء العامة"""
    logger.error(f"Error: {context.error}\n{traceback.format_exc()}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ حدث خطأ غير متوقع\nالرجاء المحاولة مرة أخرى لاحقاً"
            )
    except Exception as e:
        logger.error(f"Error in error handler: {str(e)}")

def main() -> None:
    """الدالة الرئيسية"""
    try:
        # إنشاء التطبيق
        application = Application.builder().token(TOKEN).build()

        # إنشاء معالج المحادثة
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
            ],
            states={
                CHOOSING_ACTION: [
                    CallbackQueryHandler(login_callback, pattern='^login$')
                ],
                USERNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)
                ],
                PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)
                ],
                CALLER_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_caller_id)
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            name="main_conversation",
            persistent=False
        )

        # إضافة المعالجات
        application.add_handler(conv_handler)
        application.add_error_handler(error_handler)

        # تشغيل البوت
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()
