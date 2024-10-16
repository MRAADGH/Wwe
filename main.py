from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from telethon import TelegramClient
from telethon.tl.functions.account import ReportPeerRequest
from telethon.tl.types import InputReportReasonPornography
import asyncio

# توكن البوت
BOT_TOKEN = '7492900908:AAGiiLlsafD-O4Fam6r5vP07vo2I8IeXVCc'
api_id = 16748685
api_hash = 'f0c8f7e4a7a50b5c64fd5243a256fd2f'

# إعدادات البوت
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# إعداد عميل Telegram
client = TelegramClient('hso', api_id, api_hash)

# زر البداية
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("تسليم حساب", callback_data="deliver_account"),
        InlineKeyboardButton("الإبلاغ عن قناة/مجموعة", callback_data="report_channel")
    )
    await message.answer("مرحبًا! اختر أحد الخيارات التالية:", reply_markup=keyboard)

# زر تسليم الحساب
@dp.callback_query_handler(lambda c: c.data == 'deliver_account')
async def deliver_account(callback_query: types.CallbackQuery):
    await callback_query.message.answer("يرجى إدخال رقم الهاتف مع رمز الدولة:")
    await bot.register_next_step_handler(callback_query.message, receive_phone)

async def receive_phone(message: types.Message):
    phone_number = message.text.strip()
    await client.connect()
    if not await client.is_user_authorized():
        try:
            await client.send_code_request(phone_number)
            await message.answer("تم إرسال كود التحقق، يرجى إدخاله:")
            await bot.register_next_step_handler(message, receive_code, phone_number)
        except Exception as e:
            await message.answer(f"خطأ في إرسال الكود: {str(e)}")

async def receive_code(message: types.Message, phone_number):
    code = message.text.strip()
    try:
        await client.sign_in(phone_number, code)
        await message.answer("تم تسجيل الدخول بنجاح!")
    except Exception as e:
        await message.answer(f"خطأ أثناء تسجيل الدخول: {str(e)}")

# زر الإبلاغ
@dp.callback_query_handler(lambda c: c.data == 'report_channel')
async def report_channel(callback_query: types.CallbackQuery):
    await callback_query.message.answer("يرجى إدخال اسم المستخدم أو الرابط للقناة/المجموعة:")
    await bot.register_next_step_handler(callback_query.message, receive_username)

async def receive_username(message: types.Message):
    channel_username = message.text.strip()
    try:
        await client.connect()
        channel = await client.get_entity(channel_username)

        # عرض معلومات القناة
        formatted_info = (
            f"معلومات حول القناه/المجموعه:\n"
            f"ID: {channel.id}\n"
            f"Title: {channel.title}\n"
            f"Username: {channel.username}\n"
        )
        await message.answer(formatted_info)

        # إرسال خيارات الإبلاغ
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("محتوى إباحي", callback_data="report_porn"),
            InlineKeyboardButton("محتوى عنيف", callback_data="report_violence")
        )
        await message.answer("يرجى اختيار نوع البلاغ:", reply_markup=keyboard)

    except Exception as e:
        await message.answer(f"خطأ: {str(e)}")

# أنواع البلاغات
@dp.callback_query_handler(lambda c: c.data in ['report_porn', 'report_violence'])
async def handle_report(callback_query: types.CallbackQuery):
    reason = InputReportReasonPornography() if callback_query.data == 'report_porn' else InputReportReasonViolence()
    channel_username = callback_query.message.reply_to_message.text.strip()
    
    # بدء البلاغ المتكرر
    while True:
        try:
            await client(ReportPeerRequest(peer=channel_username, reason=reason, message="بلاغ بسبب المحتوى"))
            await callback_query.message.answer(f"تم الإبلاغ عن {channel_username} بنجاح.")
            await asyncio.sleep(1)  # تأخير زمني بين البلاغات
        except Exception as e:
            await callback_query.message.answer(f"خطأ أثناء الإبلاغ: {str(e)}")
            break

# تشغيل البوت
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
