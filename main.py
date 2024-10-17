import os
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import traceback

# إعداد التسجيل المفصل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # تغيير مستوى التسجيل إلى DEBUG للحصول على مزيد من التفاصيل
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# التوكن
TOKEN = "7852676274:AAHIx3Q9qFbylmvHKDhbhT5nEpFOFA5i2CM"

# حالات المحادثة
CHOOSING_ACTION, USERNAME, PASSWORD, CALLER_ID = range(4)

# رابط الموقع
WEBSITE_URL = "http://sip.vipcaller.net"

def setup_driver():
    """إعداد متصفح Chrome مع إعدادات محسنة"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--dns-prefetch-disable")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    chrome_driver_path = os.getenv("CHROME_DRIVER_PATH", "/usr/bin/chromedriver")
    
    options.binary_location = chrome_bin
    service = Service(executable_path=chrome_driver_path)
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

async def check_website_availability():
    """التحقق من توفر الموقع"""
    try:
        driver = setup_driver()
        driver.get(WEBSITE_URL)
        time.sleep(3)  # انتظار للتأكد من تحميل الصفحة
        return True
    except Exception as e:
        logger.error(f"خطأ في الوصول للموقع: {str(e)}")
        return False
    finally:
        driver.quit()

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
    
    # التحقق من توفر الموقع قبل المتابعة
    site_available = await check_website_availability()
    if not site_available:
        await query.edit_message_text("⚠️ عذراً، الموقع غير متاح حالياً. الرجاء المحاولة لاحقاً.")
        return ConversationHandler.END
        
    await query.edit_message_text("الرجاء إدخال اسم المستخدم:")
    return USERNAME

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة إدخال اسم المستخدم"""
    username = update.message.text
    logger.info(f"تم استلام اسم المستخدم: {username}")
    context.user_data['username'] = username
    await update.message.reply_text("الرجاء إدخال كلمة المرور:")
    return PASSWORD

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة إدخال كلمة المرور"""
    try:
        username = context.user_data.get('username')
        password = update.message.text
        
        logger.info("بدء محاولة تسجيل الدخول...")
        status_message = await update.message.reply_text("جاري تسجيل الدخول... ⏳")
        
        driver = setup_driver()
        try:
            # الوصول للموقع
            logger.debug("محاولة الوصول للموقع...")
            driver.get(WEBSITE_URL)
            time.sleep(3)  # انتظار للتحميل الكامل
            
            wait = WebDriverWait(driver, 20)
            
            # التحقق من وجود حقل اسم المستخدم
            logger.debug("البحث عن حقل اسم المستخدم...")
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.clear()
            time.sleep(1)
            username_field.send_keys(username)
            logger.debug("تم إدخال اسم المستخدم")
            
            # إدخال كلمة المرور
            logger.debug("البحث عن حقل كلمة المرور...")
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            time.sleep(1)
            password_field.send_keys(password)
            logger.debug("تم إدخال كلمة المرور")
            
            # الضغط على زر تسجيل الدخول
            logger.debug("محاولة الضغط على زر تسجيل الدخول...")
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
            time.sleep(1)
            login_button.click()
            logger.debug("تم الضغط على زر تسجيل الدخول")
            
            # التحقق من نجاح تسجيل الدخول
            try:
                logger.debug("التحقق من نجاح تسجيل الدخول...")
                dashboard = wait.until(EC.presence_of_element_located((By.ID, "dashboard")))
                
                await status_message.edit_text("✅ تم تسجيل الدخول بنجاح!\nالرجاء إدخال معرف المتصل الجديد:")
                context.user_data['logged_in'] = True
                logger.info("تم تسجيل الدخول بنجاح")
                return CALLER_ID
                
            except TimeoutException:
                error_msg = "❌ فشل تسجيل الدخول\nتأكد من صحة بيانات الدخول"
                logger.error("فشل تسجيل الدخول - خطأ في التحقق من لوحة التحكم")
                await status_message.edit_text(error_msg)
                return ConversationHandler.END

        except Exception as e:
            logger.error(f"خطأ أثناء تسجيل الدخول: {str(e)}")
            logger.error(f"التفاصيل الكاملة: {traceback.format_exc()}")
            
            # التقاط لقطة شاشة للتشخيص
            try:
                driver.save_screenshot('error_screenshot.png')
                logger.info("تم حفظ لقطة شاشة للخطأ")
            except:
                logger.error("فشل في حفظ لقطة الشاشة")
            
            await status_message.edit_text(
                "❌ حدث خطأ أثناء محاولة تسجيل الدخول\n"
                "الرجاء التأكد من:\n"
                "1. صحة بيانات الدخول\n"
                "2. اتصال الإنترنت\n"
                "3. توفر الموقع\n"
                "ثم المحاولة مرة أخرى"
            )
            return ConversationHandler.END

        finally:
            logger.debug("إغلاق المتصفح...")
            driver.quit()

    except Exception as e:
        logger.error(f"خطأ عام: {str(e)}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "❌ حدث خطأ غير متوقع\n"
            "الرجاء المحاولة مرة أخرى لاحقاً"
        )
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
        # إنشاء التطبيق مع زيادة مهلة الاتصال
        application = Application.builder().token(TOKEN).connect_timeout(30).read_timeout(30).write_timeout(30).build()

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
        logger.error(f"خطأ حرج في تشغيل البوت: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()
