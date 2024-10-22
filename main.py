import telebot
import socket
import concurrent.futures
from ping3 import ping
import time
import io

TOKEN = '7852676274:AAHIx3Q9qFbylmvHKDhbhT5nEpFOFA5i2CM'
bot = telebot.TeleBot(TOKEN)

class IPScanner:
    def __init__(self, ip_list, threads=50):
        self.ip_list = ip_list
        self.threads = threads
        self.working_hosts = []

    def check_host(self, ip):
        try:
            response_time = ping(ip, timeout=2)
            if response_time is not None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip, 80))
                sock.close()
                
                if result == 0:
                    self.working_hosts.append(ip)
                    return True, ip, response_time
            return False, ip, None
        except Exception:
            return False, ip, None

    def scan(self):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_ip = {executor.submit(self.check_host, ip): ip for ip in self.ip_list}
            for future in concurrent.futures.as_completed(future_to_ip):
                try:
                    success, ip, response_time = future.result()
                    if success:
                        results.append(f"✅ {ip} - شغال - {response_time:.2f}ms")
                except Exception:
                    continue
        return results

def send_long_message(chat_id, text, reply_to_message_id=None):
    max_length = 4000
    parts = []
    
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        part = text[:max_length]
        last_newline = part.rfind('\n')
        if last_newline != -1:
            parts.append(text[:last_newline])
            text = text[last_newline + 1:]
        else:
            parts.append(text[:max_length])
            text = text[max_length:]

    first_message_id = None
    for i, part in enumerate(parts):
        if i == 0 and reply_to_message_id:
            message = bot.reply_to(reply_to_message_id, part)
            first_message_id = message.message_id
        else:
            message = bot.send_message(chat_id, part)
    
    return first_message_id

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
مرحباً بك في بوت فحص الهوستات! 🌐

الأوامر المتاحة:
- أرسل قائمة من عناوين IP للفحص
- /help للمساعدة

المطور: @aIhabeb
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
كيفية استخدام البوت:
1. قم بنسخ قائمة الهوستات (IP)
2. أرسلها مباشرة إلى البوت
3. انتظر النتائج - سيظهر لك الهوستات الشغالة فقط

مثال:
185.60.219.14
185.60.219.15
185.60.219.16
    """
    bot.reply_to(message, help_text)

@bot.message_handler(func=lambda message: True)
def scan_ips(message):
    ip_list = [ip.strip() for ip in message.text.split('\n') if ip.strip()]
    
    if not ip_list:
        bot.reply_to(message, "❌ الرجاء إرسال قائمة صحيحة من عناوين IP!")
        return

    valid_ips = []
    for ip in ip_list:
        try:
            socket.inet_aton(ip)
            valid_ips.append(ip)
        except socket.error:
            continue

    if not valid_ips:
        bot.reply_to(message, "❌ لم يتم العثور على عناوين IP صحيحة!")
        return

    status_message = bot.reply_to(message, f"⏳ جاري فحص {len(valid_ips)} هوست...")

    scanner = IPScanner(valid_ips)
    start_time = time.time()
    working_hosts = scanner.scan()
    scan_time = time.time() - start_time

    if working_hosts:
        results_text = "🟢 الهوستات الشغالة:\n\n"
        results_text += "\n".join(working_hosts)
        results_text += f"\n\n⏱ زمن الفحص: {scan_time:.2f} ثانية"
        results_text += "\n\nBY: @aIhabeb"

        bot.delete_message(message.chat.id, status_message.message_id)
        
        send_long_message(message.chat.id, results_text, message)

        results_file = io.StringIO()
        results_file.write("\n".join([host.split(" ")[1] for host in working_hosts]))
        results_file.seek(0)
        
        bot.send_document(
            message.chat.id,
            ('working_hosts.txt', results_file.getvalue().encode()),
            caption=f"📄 تم العثور على {len(working_hosts)} هوست شغال"
        )
    else:
        bot.edit_message_text(
            f"❌ لم يتم العثور على هوستات شغالة\n⏱ زمن الفحص: {scan_time:.2f} ثانية",
            message.chat.id,
            status_message.message_id
        )

if __name__ == "__main__":
    print("Bot started...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Error: {e}")
