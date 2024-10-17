
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

# توكن البوت - قم بتغييره إلى التوكن الخاص بك
TOKEN = "7852676274:AAHIx3Q9qFbylmvHKDhbhT5nEpFOFA5i2CM"

# حالات المحادثة
USERNAME, PASSWORD, CALLER_ID = range(3)

# رابط الموقع - قم بتغييره إلى الرابط الخاص بك
WEBSITE_URL = "http://sip.vipcaller.net/mbilling/"

# تخزين جلسة المتصفح
driver = None

def setup_chrome_options():
    """إعداد خيارات متصفح كروم"""
    options = Options()
    options.add_argument("--headless")  # تشغيل المتصفح بدون واجهة رسومية
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return options

def create_driver():
    """إنشاء متصفح جديد"""
    options = setup_chrome_options()
    service = Service()  # قم بتحديد مسار ChromeDriver إذا كان ضرورياً
    new_driver = webdriver.Chrome(service=service, options=options)
    new_driver.implicitly_wait(10)
    return new_driver

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
    # حذف رسالة المستخدم التي تحتوي على اسم المستخدم لأسباب أمنية
    await update.message.delete()
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج استلام كلمة المرور ومحاولة تسجيل الدخول"""
    # حذف رسالة المستخدم التي تحتوي على كلمة المرور لأسباب أمنية
    await update.message.delete()
    
    try:
        username = context.user_data['username']
        password = update.message.text
        
        driver = create_driver()
        driver.get(WEBSITE_URL)
        
        wait = WebDriverWait(driver, 30)
        
        # إدخال اسم المستخدم
        username_field = wait.until(
            EC.element_to_be_clickable((By.ID, "username"))
        )
        username_field.clear()
        username_field.send_keys(username)
        
        # إدخال كلمة المرور
        password_field = wait.until(
            EC.element_to_be_clickable((By.ID, "password"))
        )
        password_field.clear()
        password_field.send_keys(password)
        
        # الضغط على زر تسجيل الدخول
        login_button = wait.until(
            EC.element_to_be_clickable((By.ID, "login-button"))
        )
        login_button.click()
        
        # التحقق من نجاح تسجيل الدخول
        try:
            # انتظار ظهور لوحة التحكم
            wait.until(EC.presence_of_element_located((By.ID, "dashboard")))
            await update.message.reply_text(
                "✅ تم تسجيل الدخول بنجاح!\n\n"
                "الرجاء إدخال معرف المتصل الجديد:"
            )
            return CALLER_ID
        except TimeoutException:
            await update.message.reply_text(
                "❌ فشل تسجيل الدخول\n"
                "تأكد من صحة اسم المستخدم وكلمة المرور"
            )
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"خطأ: {str(e)}")
        await update.message.reply_text(
            "❌ حدث خطأ غير متوقع\n"
            "الرجاء المحاولة مرة أخرى لاحقاً"
        )
        return ConversationHandler.END
        
    finally:
        if driver:
            driver.quit()

async def change_caller_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج تغيير معرف المتصل"""
    new_caller_id = update.message.text
    
    try:
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
        per_message=True  # تمكين تتبع الحالة لكل رسالة
    )
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    
    # تشغيل البوت
    application.run_polling()

if __name__ == '__main__':
    main()
