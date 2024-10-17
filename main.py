import os
import logging
import traceback
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


import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
# التوكن
TOKEN = "7852676274:AAHIx3Q9qFbylmvHKDhbhT5nEpFOFA5i2CM"

# حالات المحادثة
USERNAME, PASSWORD, CALLER_ID = range(3)

# رابط الموقع
WEBSITE_URL = "http://sip.vipcaller.net/mbilling/"

# إعدادات المتصفح
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium")
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER", "/usr/bin/chromedriver")

def setup_driver():
    """إعداد متصفح Chrome"""
    options = Options()
    options.binary_location = CHROME_BIN
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    service = Service(executable_path=CHROME_DRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء العامة"""
    logger.error(f"حدث خطأ: {context.error}")
    logger.error(traceback.format_exc())
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "عذراً، حدث خطأ أثناء تنفيذ العملية. الرجاء المحاولة مرة أخرى."
            )
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية المحادثة"""
    keyboard = [[InlineKeyboardButton("تسجيل الدخول", callback_data='login')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'مرحباً بك في بوت تغيير معرف المتصل\nاضغط على زر تسجيل الدخول للبدء',
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def handle_login_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة زر تسجيل الدخول"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("الرجاء إدخال اسم المستخدم:")
    return USERNAME

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة اسم المستخدم"""
    context.user_data['username'] = update.message.text
    await update.message.reply_text("الرجاء إدخال كلمة المرور:")
    return PASSWORD

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة كلمة المرور"""
    try:
        username = context.user_data.get('username')
        password = update.message.text

        if not username:
            await update.message.reply_text("خطأ: لم يتم العثور على اسم المستخدم. الرجاء البدء من جديد باستخدام /start")
            return ConversationHandler.END

        driver = setup_driver()
        try:
            # فتح صفحة تسجيل الدخول
            driver.get(WEBSITE_URL)
            wait = WebDriverWait(driver, 20)

            # إدخال اسم المستخدم
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.clear()
            username_field.send_keys(username)

            # إدخال كلمة المرور
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)

            # الضغط على زر تسجيل الدخول
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
            login_button.click()

            # التحقق من نجاح تسجيل الدخول
            try:
                dashboard = wait.until(EC.presence_of_element_located((By.ID, "dashboard")))
                await update.message.reply_text(
                    "✅ تم تسجيل الدخول بنجاح!\nالرجاء إدخال معرف المتصل الجديد:"
                )
                context.user_data['logged_in'] = True
                return CALLER_ID
            except TimeoutException:
                await update.message.reply_text(
                    "❌ فشل تسجيل الدخول\nتأكد من صحة اسم المستخدم وكلمة المرور"
                )
                return ConversationHandler.END

        except Exception as e:
            logger.error(f"خطأ في عملية تسجيل الدخول: {str(e)}")
            await update.message.reply_text(
                "❌ حدث خطأ أثناء محاولة تسجيل الدخول\nالرجاء المحاولة مرة أخرى"
            )
            return ConversationHandler.END

        finally:
            driver.quit()

    except Exception as e:
        logger.error(f"خطأ غير متوقع: {str(e)}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "❌ حدث خطأ غير متوقع\nالرجاء المحاولة مرة أخرى"
        )
        return ConversationHandler.END

async def handle_caller_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة تغيير معرف المتصل"""
    if not context.user_data.get('logged_in'):
        await update.message.reply_text("الرجاء تسجيل الدخول أولاً")
        return ConversationHandler.END

    new_caller_id = update.message.text
    driver = None
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 20)

        # تغيير معرف المتصل
        caller_id_field = wait.until(EC.presence_of_element_located((By.ID, "caller-id")))
        caller_id_field.clear()
        caller_id_field.send_keys(new_caller_id)

        save_button = wait.until(EC.element_to_be_clickable((By.ID, "save-button")))
        save_button.click()

        await update.message.reply_text(f"✅ تم تغيير معرف المتصل بنجاح إلى: {new_caller_id}")
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"خطأ في تغيير معرف المتصل: {str(e)}")
        await update.message.reply_text("❌ حدث خطأ أثناء تغيير معرف المتصل")
        return ConversationHandler.END

    finally:
        if driver:
            driver.quit()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء المحادثة"""
    await update.message.reply_text('تم إلغاء العملية')
    return ConversationHandler.END

def main() -> None:
    """الدالة الرئيسية"""
    try:
        # إنشاء التطبيق
        application = Application.builder().token(TOKEN).build()

        # إضافة معالج المحادثة
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                CallbackQueryHandler(handle_login_button, pattern='^login$')
            ],
            states={
                USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)],
                PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
                CALLER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_caller_id)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            name="main_conversation",
            persistent=False
        )

        # إضافة المعالجات
        application.add_handler(conv_handler)
        application.add_error_handler(error_handler)

        # تشغيل البوت
        logger.info("بدء تشغيل البوت...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {str(e)}")
        logger.error(traceback.format_exc())
        # إعادة المحاولة بعد فترة
        import time
        time.sleep(60)  # انتظر دقيقة واحدة
        main()  # أعد تشغيل البوت

if __name__ == '__main__':
    main()
