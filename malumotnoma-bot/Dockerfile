FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libreoffice-writer \
       libreoffice-core \
       fonts-liberation \
       fonts-dejavu \
       fontconfig \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY shablon.docx .

RUN mkdir -p /app/downloads

CMD ["python", "bot.py"]
