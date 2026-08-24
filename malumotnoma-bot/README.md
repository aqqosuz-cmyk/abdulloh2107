# Ma'lumotnoma Telegram Bot

Telegram bot foydalanuvchidan ma'lumotlarni yig'adi, Word shablonini to'ldiradi, tayyor hujjatning `NAMUNA` watermarkli preview rasmini yuboradi va to'lov chekini administratorga yuborib, admin tasdiqlagandan keyin original `.docx` faylni foydalanuvchiga jo'natadi.

## Muhim

Bot preview yaratish uchun **Windows + Microsoft Word desktop** kerak. Python `pywin32` orqali Word'ni boshqaradi. GitHub kodni saqlash uchun ishlatiladi; botni Windows kompyuterda ishga tushiring.

## Papka tarkibi

```text
malumotnoma_bot/
├── bot.py
├── shablon.docx
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 1. Python

Python 3.10+ tavsiya qilinadi.

## 2. Kutubxonalar

CMD:

```bash
pip install -r requirements.txt
```

## 3. Microsoft Word

Kompyuterda Microsoft Word desktop o'rnatilgan bo'lishi kerak.

## 4. `.env`

`.env.example` nusxasini `.env` nomi bilan saqlang va tokenni kiriting:

```text
BOT_TOKEN=...
ADMIN_ID=7737099509
PAYMENT_CARD=...
CARD_OWNER=Ergashev Tohirjon
PAYMENT_AMOUNT=30 000 so'm
SUPPORT_PHONE=908909199
PROMO_CODE=asm2107
```

`.env` GitHub'ga yuklanmasligi kerak.

## 5. Ishga tushirish

```bash
python bot.py
```

## Ishlash tartibi

1. Foydalanuvchi `START` orqali anketani boshlaydi.
2. Savollarga javob beradi.
3. Har bir savolda `YO'Q` tugmasi mavjud.
4. Rasm oddiy Telegram photo yoki image file sifatida qabul qilinadi.
5. DOCX shablon bilan to'ldiriladi.
6. Word orqali preview tayyorlanadi.
7. Preview sahifalariga diagonal `NAMUNA` watermark qo'yiladi.
8. Preview foydalanuvchiga yuboriladi.
9. Keyin 30 000 so'mlik to'lov ma'lumotlari chiqadi.
10. Foydalanuvchi chek yuboradi.
11. Chek admin ID'ga yuboriladi.
12. Admin `TASDIQLASH` yoki `RAD ETISH` tugmasini bosadi.
13. Tasdiqlansa original DOCX yuboriladi va `START` yana chiqadi.
14. Rad etilsa foydalanuvchidan chekni qayta yuborish so'raladi.

## GitHub

```bash
git init
git add .
git commit -m "Initial bot"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

**Bot tokeni, karta raqami yoki boshqa maxfiy ma'lumotlarni GitHub'ga ochiq yuklamang.** `.env` faqat lokal kompyuterda bo'lsin.

## Botni ikki marta ishga tushirmang

Bir xil bot token bilan bir vaqtning o'zida faqat bitta polling jarayoni ishlasin. Aks holda Telegram `TelegramConflictError: terminated by other getUpdates request` qaytaradi.

## Eslatma

Hozirgi versiyada to'lov kutayotgan hujjatlar RAM'dagi `pending_payments` dictionary'da saqlanadi. Bot restart qilinsa tasdiqlanmagan sessiyalar yo'qolishi mumkin. Ishlab chiqarish uchun keyingi bosqichda SQLite/PostgreSQL saqlashni qo'shish tavsiya qilinadi.
