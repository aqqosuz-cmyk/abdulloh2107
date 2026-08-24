FROM python:3.10-slim

WORKDIR /app

# Kerakli tizim kutubxonalarini o'rnatish
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Talab qilinadigan kutubxonalarni ko'chirish va o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Qolgan barcha fayllarni ko'chirish
COPY . .

# Botni ishga tushirish
CMD ["python", "main.py"]
