import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, ContextTypes
import traceback

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# التوكن
TOKEN = "6845291404:AAHn2aPymNMuMeHZtQ470jKJJJ08YRjpaOI"

# حالات المحادثة
CHOOSING_ACTION, USERNAME, PASSWORD, CALLER_ID = range(4)

# رابط الموقع
WEBSITE_URL = "http://sip.vipcaller.net/mbilling/"

# التحقق من توفر الموقع
def check_website_availability():
    """التحقق من توفر الموقع باستخدام requests"""
    try:
        response = requests.get(WEBSITE_URL, timeout=10)
        if response.status_code == 200:
            logger.info("الموقع متاح")
            return True
        else:
            logger.warning(f"الموقع غير متاح، رمز الاستجابة: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"خطأ في التحقق من الموقع: {str(e)}")
        return False

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
    
    site_available = check_website_availability()
    if not site_available:
        await query.edit_message_text("⚠️ عذراً، الموقع غير متاح حالياً. الرجاء المحاولة لاحقاً.")
        return ConversationHandler.END
        
    await query.edit_message_text("الرجاء إدخال اسم المستخدم:")
    return USERNAME

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة إدخال اسم المستخدم"""
    username = update.message.text
    context.user_data['username'] = username
    await update.message.reply_text("الرجاء إدخال كلمة المرور:")
    return PASSWORD

async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة إدخال كلمة المرور"""
    username = context.user_data.get('username')
    password = update.message.text
    
    logger.info("بدء محاولة تسجيل الدخول...")
    status_message = await update.message.reply_text("جاري تسجيل الدخول... ⏳")
    
    try:
        # هنا يمكنك تعديل الكود ليستخدم requests لتسجيل الدخول إذا كان الموقع يدعم ذلك
        login_data = {'username': username, 'password': password}
        response = requests.post(WEBSITE_URL, data=login_data)
        
        if response.status_code == 200:
            await status_message.edit_text("✅ تم تسجيل الدخول بنجاح!\nالرجاء إدخال معرف المتصل الجديد:")
            context.user_data['logged_in'] = True
            return CALLER_ID
        else:
            await status_message.edit_text("❌ فشل تسجيل الدخول\nتأكد من صحة بيانات الدخول")
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"خطأ أثناء تسجيل الدخول: {str(e)}")
        await status_message.edit_text("❌ حدث خطأ أثناء محاولة تسجيل الدخول")
        return ConversationHandler.END

async def handle_caller_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة تغيير معرف المتصل"""
    if not context.user_data.get('logged_in'):
        await update.message.reply_text("الرجاء تسجيل الدخول أولاً")
        return ConversationHandler.END

    status_message = await update.message.reply_text("جاري تغيير معرف المتصل...")
    new_caller_id = update.message.text
    
    try:
        # قم بإرسال معرف المتصل الجديد باستخدام requests أو أي طريقة متاحة
        response = requests.post(WEBSITE_URL, data={'caller_id': new_caller_id})
        
        if response.status_code == 200:
            await status_message.edit_text(f"✅ تم تغيير معرف المتصل بنجاح إلى: {new_caller_id}")
        else:
            await status_message.edit_text("❌ حدث خطأ أثناء تغيير معرف المتصل")
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"خطأ في تغيير معرف المتصل: {str(e)}")
        await status_message.edit_text("❌ حدث خطأ أثناء تغيير معرف المتصل")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء العملية"""
    await update.message.reply_text('تم إلغاء العملية')
    return ConversationHandler.END

def main() -> None:
    """الدالة الرئيسية"""
    try:
        application = Application.builder().token(TOKEN).connect_timeout(60).read_timeout(60).write_timeout(60).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                CHOOSING_ACTION: [CallbackQueryHandler(login_callback, pattern='^login$')],
                USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)],
                PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)],
                CALLER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_caller_id)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            name="main_conversation",
            persistent=False
        )

        application.add_handler(conv_handler)

        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"خطأ حرج في تشغيل البوت: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()
