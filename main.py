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
from webdriver_manager.chrome import ChromeDriverManager

# إعداد التسجيل بشكل أكثر تفصيلاً
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# التوكن
TOKEN = "7492900908:AAGiiLlsafD-O4Fam6r5vP07vo2I8IeXVCc"  # استبدل بالتوكن الخاص بك

# حالات المحادثة
USERNAME, PASSWORD, CALLER_ID = range(3)

# رابط الموقع
WEBSITE_URL = "http://sip.vipcaller.net/mbilling/"

def setup_driver():
    """إعداد متصفح Chrome مع معالجة أفضل للأخطاء"""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # استخدام webdriver_manager للحصول على ChromeDriver المناسب
        service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logger.error(f"خطأ في إعداد المتصفح: {str(e)}")
        raise

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء المحسن"""
    logger.error(f"Exception while handling an update: {context.error}")
    logger.error(traceback.format_exc())
    
    error_message = "عذراً، حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى لاحقاً."
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(error_message)
    except Exception as e:
        logger.error(f"Error sending error message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية المحادثة"""
    try:
        keyboard = [[InlineKeyboardButton("تسجيل الدخول", callback_data='login')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            'مرحباً بك في بوت تغيير معرف المتصل\nاضغط على زر تسجيل الدخول للبدء',
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await error_handler(update, context)
        return ConversationHandler.END

async def handle_login_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة زر تسجيل الدخول"""
    try:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("الرجاء إدخال اسم المستخدم:")
        return USERNAME
    except Exception as e:
        logger.error(f"Error in login button handler: {e}")
        await error_handler(update, context)
        return ConversationHandler.END

# ... (باقي الدوال تبقى كما هي مع إضافة معالجة الأخطاء المناسبة)

def main() -> None:
    """الدالة الرئيسية المحسنة"""
    try:
        # إنشاء التطبيق مع إعدادات إضافية
        application = Application.builder().token(TOKEN).connect_timeout(30).read_timeout(30).build()

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

        application.add_handler(conv_handler)
        application.add_error_handler(error_handler)

        # تشغيل البوت مع إعدادات إضافية
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            pool_timeout=30
        )

    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        logger.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    main()
