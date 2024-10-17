import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import asyncio

# استبدلها بالرمز الخاص بك
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# حالات المحادثة
USERNAME, PASSWORD, CALLER_ID = range(3)

# استبدلها برابط الموقع الخاص بك
WEBSITE_URL = "http://sip.vipcaller.net/mbilling/"

# إعداد خيارات Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  # للتشغيل بدون واجهة
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.binary_location = "/usr/bin/google-chrome"  # مسار Chrome داخل الحاوية

# تهيئة WebDriver
driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=chrome_options)

# تعريف الوظائف الخاصة بالبوت

async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("تسجيل الدخول", callback_data='login')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('مرحبًا بك في بوت خدمة تغيير معرف المتصل. الرجاء تسجيل الدخول.', reply_markup=reply_markup)

async def login(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="📳 خدمة تغيير معرف المتصل | قائمة تسجيل الدخول\n\nℹ️ أدخل اسم المستخدم الخاص بك:")
    return USERNAME

async def get_username(update: Update, context):
    context.user_data['username'] = update.message.text
    await update.message.reply_text("📳 خدمة تغيير معرف المتصل | قائمة تسجيل الدخول\n\nℹ️ أدخل كلمة المرور الخاصة بك:")
    return PASSWORD

async def get_password(update: Update, context):
    username = context.user_data['username']
    password = update.message.text

    # الدخول إلى الموقع باستخدام Selenium
    driver.get(WEBSITE_URL)

    # انتظار ظهور حقل اسم المستخدم وإدخال البيانات
    username_field = WebDriverWait(driver, 10).until(
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
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "dashboard"))
        )
        await update.message.reply_text("🔔 تم تسجيل الدخول بنجاح ✅\n\nℹ️ أدخل معرف المتصل الذي تريد إظهاره:")
        return CALLER_ID
    except:
        await update.message.reply_text("❌ فشل تسجيل الدخول. الرجاء المحاولة مرة أخرى.")
        return ConversationHandler.END

async def change_caller_id(update: Update, context):
    new_caller_id = update.message.text

    # تغيير معرف المتصل باستخدام Selenium
    try:
        caller_id_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "caller-id"))
        )
        caller_id_field.clear()
        caller_id_field.send_keys(new_caller_id)

        save_button = driver.find_element(By.ID, "save-caller-id")
        save_button.click()

        # انتظار رسالة التأكيد
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "success-message"))
        )

        await update.message.reply_text(f"✅ تم تحديث معرف المتصل بنجاح: {new_caller_id}")
    except:
        await update.message.reply_text("❌ حدث خطأ أثناء تحديث معرف المتصل. الرجاء المحاولة مرة أخرى.")

    return ConversationHandler.END

async def cancel(update: Update, context):
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
