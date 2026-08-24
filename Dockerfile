FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Kerakli tizim kutubxonalari (ffmpeg va build vositalari)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Talab qilinadigan kutubxonalarni ko'chirish va o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Qolgan barcha fayllarni konteynerga ko'chirish
COPY . .

# Barcha botlarni (jumladan resume.py ni ham) boshqaruvchi launcher orqali ishga tushirish
CMD ["python", "launcher.py"]
