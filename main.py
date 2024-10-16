from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneNumberOccupiedError
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import logging

# إعدادات API وTelegram bot
BOT_TOKEN = '7852676274:AAHIx3Q9qFbylmvHKDhbhT5nEpFOFA5i2CM'
api_id = 16748685
api_hash = 'f0c8f7e4a7a50b5c64fd5243a256fd2f'

# تشغيل تسجيل الأخطاء
logging.basicConfig(level=logging.INFO)

# إعداد البوت وTelethon client
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
client = TelegramClient('session_name', api_id, api_hash)

# إعداد حالة لحفظ رقم الهاتف
user_phone = {}

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("مرحبًا! لإتمام عملية تسليم الحساب، أرسل رقم الهاتف مع رمز الدولة:")

@dp.message_handler()
async def receive_phone(message: types.Message):
    phone_number = message.text.strip()
    try:
        await client.connect()
        
        # التحقق إذا كان المستخدم مسجل بالفعل
        if await client.is_user_authorized():
            await message.reply("الرقم مسجل مسبقًا.")
        else:
            try:
                # طلب كود التحقق وإظهار رسالة
                await client.send_code_request(phone_number)
                user_phone[message.from_user.id] = phone_number
                await message.reply("تم إرسال كود التحقق، يرجى إدخاله الآن:")
                
            except PhoneNumberOccupiedError:
                await message.reply("هذا الرقم مسجل مسبقًا. يرجى استخدام رقم آخر.")
    except Exception as e:
        await message.reply(f"حدث خطأ: {str(e)}")

# استلام كود التحقق
@dp.message_handler(lambda message: message.from_user.id in user_phone)
async def receive_code(message: types.Message):
    phone_number = user_phone[message.from_user.id]
    code = message.text.strip()
    
    try:
        await client.sign_in(phone_number, code)
        await message.reply("تم تسجيل الدخول بنجاح!")
    except SessionPasswordNeededError:
        await message.reply("التحقق بخطوتين مطلوب، يرجى إدخال كلمة المرور:")
    except Exception as e:
        await message.reply(f"خطأ أثناء تسجيل الدخول: {str(e)}")

@dp.message_handler(lambda message: 'كلمة المرور' in message.text)
async def receive_password(message: types.Message):
    password = message.text.strip()
    
    try:
        await client.sign_in(password=password)
        await message.reply("تم تسجيل الدخول بنجاح!")
    except Exception as e:
        await message.reply(f"خطأ أثناء إدخال كلمة المرور: {str(e)}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
