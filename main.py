from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged
import asyncio
import aiohttp

# تفاصيل API الخاصة بك
API_ID = '16748685'
API_HASH = 'f0c8f7e4a7a50b5c64fd5243a256fd2f'
BOT_TOKEN = '7492900908:AAGiiLlsafD-O4Fam6r5vP07vo2I8IeXVCc'

# إعداد الـ Headers لمحاكاة جهاز حقيقي
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.127 Mobile Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Connection': 'keep-alive'
}

async def create_session():
    """إنشاء جلسة aiohttp مع Headers مخصصة"""
    session = aiohttp.ClientSession(headers=headers)
    return session

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("تسجيل حساب", callback_data='register')],
        [InlineKeyboardButton("إبلاغ", callback_data='report')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('مرحبًا! اختر ما تريد القيام به:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'register':
        await query.edit_message_text(text="الرجاء إدخال رقم هاتفك مع رمز الدولة (مثال: +1234567890):")
        return 'PHONE'
    elif query.data == 'report':
        await query.edit_message_text(text="الرجاء إدخال اسم المستخدم أو رابط القناة/المجموعة التي تريد الإبلاغ عنها:")
        return 'CHANNEL'

async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    phone = update.message.text
    
    # إنشاء جلسة aiohttp مع Headers
    session = await create_session()

    # تمرير الجلسة إلى TelegramClient
    client = TelegramClient(f'session_{user_id}', API_ID, API_HASH, connection=ConnectionTcpAbridged, session=session)

    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            sent_code = await client.send_code_request(phone)
            await update.message.reply_text("تم إرسال رمز التحقق. الرجاء إدخاله:")
            return 'CODE'
        else:
            await update.message.reply_text("تم تسجيل الدخول بنجاح!")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء محاولة تسجيل الدخول: {str(e)}")

async def verification_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    code = update.message.text

    session = await create_session()
    client = TelegramClient(f'session_{user_id}', API_ID, API_HASH, connection=ConnectionTcpAbridged, session=session)

    try:
        await client.connect()
        await client.sign_in(user_data[user_id]['phone'], code)
        await update.message.reply_text("تم تسجيل الدخول بنجاح!")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ: {str(e)}")

async def channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    channel_username = update.message.text
    user_id = update.effective_user.id

    session = await create_session()
    client = TelegramClient(f'session_{user_id}', API_ID, API_HASH, connection=ConnectionTcpAbridged, session=session)

    try:
        await client.connect()
        channel = await client.get_entity(channel_username)
        info = (
            f"معلومات القناة/المجموعة:\n"
            f"الاسم: {channel.title}\n"
            f"المعرف: {channel.username if hasattr(channel, 'username') else 'غير متاح'}\n"
            f"الوصف: {channel.about if hasattr(channel, 'about') else 'غير متاح'}\n"
            f"عدد المشتركين: {channel.participants_count if hasattr(channel, 'participants_count') else 'غير متاح'}"
        )
        
        keyboard = [
            [InlineKeyboardButton("محتوى إباحي", callback_data='report_porn')],
            [InlineKeyboardButton("عنف", callback_data='report_violence')],
            [InlineKeyboardButton("سبام", callback_data='report_spam')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(info, reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ: {str(e)}")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.Regex(r'^\+\d+$') & ~filters.COMMAND, phone_number))
    application.add_handler(MessageHandler(filters.Regex(r'^\d+$') & ~filters.COMMAND, verification_code))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, channel_info))

    application.run_polling()

if __name__ == '__main__':
    main()
