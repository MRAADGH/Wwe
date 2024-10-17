# استخدام الإصدار المطلوب من بايثون
FROM python:3.11-slim

# تثبيت الحزم اللازمة
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# تعيين متغير البيئة ليعمل Chromium كسيناريو دون واجهة
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER_PATH=/usr/bin/chromedriver

# نسخ المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات البرمجية
COPY . .

# تشغيل البرنامج
CMD ["python", "main.py"]
