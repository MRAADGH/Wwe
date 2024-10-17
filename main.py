
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
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# استبدلها بالرمز الخاص بك
TOKEN = "7852676274:AAHIx3Q9qFbylmvHKDhbhT5nEpFOFA5i2CM"

# حالات المحادثة
USERNAME, PASSWORD, CALLER_ID = range(3)

# استبدلها برابط الموقع الخاص بك
WEBSITE_URL = "http://sip.vipcaller.net/"

# إعداد خيارات Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# تحديد مسارات المتصفح Chromium و ChromeDriver من البيئة
chrome_options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
chrome_driver_path = os.getenv("CHROME_DRIVER", "/usr/bin/chromedriver")

# تهيئة WebDriver
driver = None

def init_driver():
    global driver
    if driver is None:
        driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
    return driver

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("تسجيل الدخول", callback_data='login')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('مرحبًا بك في بوت خدمة تغيير معرف المتصل. الرجاء تسجيل الدخول.', reply_markup=reply_markup)

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="📳 خدمة تغيير معرف المتصل | قائمة تسجيل الدخول\n\nℹ️ أدخل اسم المستخدم الخاص بك:")
    return USERNAME

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['username'] = update.message.text
    await update.message.reply_text("📳 خدمة تغيير معرف المتصل | قائمة تسجيل الدخول\n\nℹ️ أدخل كلمة المرور الخاصة بك:")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = context.user_data['username']
    password = update.message.text

    try:
        driver = init_driver()
        driver.get(WEBSITE_URL)

        # انتظار ظهور حقل اسم المستخدم وإدخال البيانات
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_field.send_keys(username)

        # إدخال كلمة المرور
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)

        # الضغط على زر الدخول
        login_button = driver.find_element(By.ID, "login-button")
        login_button.click()

        # التحقق من نجاح تسجيل الدخول
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "dashboard"))
        )
        await update.message.reply_text("🔔 تم تسجيل الدخول بنجاح ✅\n\nℹ️ أدخل معرف المتصل الذي تريد إظهاره:")
        return CALLER_ID
    except TimeoutException:
        await update.message.reply_text("❌ انتهت مهلة تسجيل الدخول. يرجى المحاولة مرة أخرى.")
    except NoSuchElementException:
        await update.message.reply_text("❌ لم يتم العثور على عناصر الصفحة. يرجى التحقق من الموقع والمحاولة مرة أخرى.")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تسجيل الدخول: {str(e)}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى لاحقًا.")
    return ConversationHandler.END

async def change_caller_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_caller_id = update.message.text

    try:
        driver = init_driver()
        caller_id_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "caller-id"))
        )
        caller_id_field.clear()
        caller_id_field.send_keys(new_caller_id)

        save_button = driver.find_element(By.ID, "save-caller-id")
        save_button.click()

        # انتظار رسالة التأكيد
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "success-message"))
        )

        await update.message.reply_text(f"✅ تم تحديث معرف المتصل بنجاح: {new_caller_id}")
    except TimeoutException:
        await update.message.reply_text("❌ انتهت مهلة تحديث معرف المتصل. يرجى المحاولة مرة أخرى.")
    except NoSuchElementException:
        await update.message.reply_text("❌ لم يتم العثور على عناصر الصفحة. يرجى التحقق من الموقع والمحاولة مرة أخرى.")
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تحديث معرف المتصل: {str(e)}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى لاحقًا.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('تم إلغاء العملية.')
    return ConversationHandler.END

def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(login, pattern='^login$')],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
            CALLER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_caller_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
