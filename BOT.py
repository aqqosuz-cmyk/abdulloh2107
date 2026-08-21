import asyncio
import io
import logging
import re
import sqlite3
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    ContentType,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
import qrcode

# Token va IDlar
TOKEN = "8830593585:AAFbI3UwrgYNqYpK7tds9LYS-AsvKqjnNQA"
SERVER_ID = -1004423144311
CHECK_CHANNEL_ID = -1003992475947  # Tekshiriladigan kanal ID si

logging.basicConfig(level=logging.INFO)
router = Router()

# SQLite bazasi
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()

# 1. Foydalanuvchilar jadvali
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        phone TEXT,
        message_id INTEGER
    )
""")

# 2. Kanal postlari jadvali
cursor.execute("""
    CREATE TABLE IF NOT EXISTS allowed_posts (
        message_id INTEGER PRIMARY KEY,
        phone_digits TEXT
    )
""")
db.commit()


class AlbumState(StatesGroup):
    waiting_for_files = State()
    waiting_for_contact = State()


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def generate_qr_code(link: str) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output.read()


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 Fayl yuborish")],
            [
                KeyboardButton(text="📖 Botning ishlash tartibi"),
                KeyboardButton(text="📞 Biz bilan aloqa"),
            ],
            [
                KeyboardButton(text="📸 Instagram (@vinetka24)"),
                KeyboardButton(text="📢 Telegram server (@vinetka24)"),
            ],
            [KeyboardButton(text="/start")],
        ],
        resize_keyboard=True,
    )


# --- KANAL TARIXINI O'QIB BAZAGA YAZISH (AVTOMATIK SKANER) ---
async def scan_channel_history(bot: Bot):
    """Bot ishga tushganda kanaldagi eski xabarlarni o'qib bazaga yig'adi"""
    print("Kanal tarixi skaner qilinmoqda...")
    try:
        # Telegram Bot API orqali kanalning oxirgi xabarlarini bevosita olib bo'lmaydi (getHistory faqat UserBotda ishlaydi).
        # Shuning uchun eng so'nggi xabar ID sini topib, sikl orqali orqaga qarab tekshirib chiqamiz:
        # Lekin oddiyroq va ishlaydigan usul: Kanalga oxirgi yozilgan xabarlarni tekshirish uchun 
        # bot o'zi ishga tushgandan keyin kelgan xabarlarni ushlaydi. 
        # Eski xabarlarni avtomatik tahrirlash uchun esa kanal egasi bir marta postlarni tahrirlashi kerak 
        # yoki biz oxirgi N ta xabar ID sini manual tekshirib chiqishimiz mumkin.
        pass
    except Exception as e:
        print(f"Skaner qilishda xatolik: {e}")


# --- KANALGA POST YOZILGANDA BAZAGA QO'SHISH ---
@router.channel_post()
async def channel_post_handler(message: Message):
    if message.chat.id == CHECK_CHANNEL_ID and message.text:
        digits = re.sub(r"\D", "", message.text)
        if len(digits) >= 9:
            last_9 = digits[-9:]
            cursor.execute(
                "INSERT OR REPLACE INTO allowed_posts (message_id, phone_digits) VALUES (?, ?)",
                (message.message_id, last_9),
            )
            db.commit()


@router.edited_channel_post()
async def edited_channel_post_handler(message: Message):
    if message.chat.id == CHECK_CHANNEL_ID:
        if message.text:
            digits = re.sub(r"\D", "", message.text)
            if len(digits) >= 9:
                last_9 = digits[-9:]
                cursor.execute(
                    "INSERT OR REPLACE INTO allowed_posts (message_id, phone_digits) VALUES (?, ?)",
                    (message.message_id, last_9),
                )
            else:
                cursor.execute(
                    "DELETE FROM allowed_posts WHERE message_id = ?",
                    (message.message_id,),
                )
        else:
            cursor.execute(
                "DELETE FROM allowed_posts WHERE message_id = ?", (message.message_id,)
            )
        db.commit()


async def find_message_id_in_channel(phone: str):
    user_digits = re.sub(r"\D", "", phone)
    user_last_9 = user_digits[-9:] if len(user_digits) >= 9 else user_digits

    if not user_last_9 or len(user_last_9) < 9:
        return None

    cursor.execute(
        "SELECT message_id FROM allowed_posts WHERE phone_digits = ?",
        (user_last_9,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


async def check_user_access(user_id: int, bot: Bot) -> bool:
    cursor.execute(
        "SELECT phone, message_id FROM users WHERE user_id = ?", (user_id,)
    )
    user_row = cursor.fetchone()
    if not user_row:
        return False
    
    phone = user_row[0]
    msg_id = await find_message_id_in_channel(phone)
    if not msg_id:
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        db.commit()
        return False

    return True


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()

    if await check_user_access(message.from_user.id, bot):
        await message.answer(
            "✅ Siz ro'yxatdan o'tgansiz va raqamingiz bazada mavjud.",
            reply_markup=get_main_menu(),
        )
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        "🔒 **Xavfsizlik tekshiruvi**\n\nBotdan foydalanish uchun telefon raqamingizni yuboring:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
    await state.set_state(AlbumState.waiting_for_contact)


@router.message(AlbumState.waiting_for_contact, F.contact)
async def check_contact(message: Message, state: FSMContext, bot: Bot):
    phone = message.contact.phone_number
    wait_msg = await message.answer(
        "🔍 Raqamingiz kanaldan va bazadan tekshirilmoqda..."
    )

    msg_id = await find_message_id_in_channel(phone)

    try:
        await bot.delete_message(
            chat_id=message.chat.id, message_id=wait_msg.message_id
        )
    except:
        pass

    if msg_id:
        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, phone, message_id) VALUES (?, ?, ?)",
            (message.from_user.id, phone, msg_id),
        )
        db.commit()

        await message.answer(
            "✅ **Tabriklaymiz! Raqamingiz tasdiqlandi.**\nEndi botdan to'liq foydalanishingiz mumkin.",
            reply_markup=get_main_menu(),
            parse_mode="Markdown",
        )
        await state.clear()
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        user_digits = re.sub(r"\D", "", phone)
        user_last_9 = user_digits[-9:] if len(user_digits) >= 9 else user_digits
        await message.answer(
            "❌ **Bu telefon raqam kanal bazasida topilmadi!**\n"
            f"(Tekshirilgan oxirgi 9 raqam: <code>{user_last_9}</code>)\n\nQaytadan urinib ko'ring:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )


@router.message(F.text == "📖 Botning ishlash tartibi")
async def help_instruction(message: Message):
    text = (
        "📋 **VINETKA24 — Botdan Foydalanish Tartibi:**\n\n"
        "1️⃣ <b>'📁 Fayl yuborish'</b> tugmasini bosing.\n"
        "2️⃣ Kerakli fayllarni yuboring va <b>'✅ Fayllarni yuborib bo'ldim (Tugatish)'</b> ni bosing.\n"
        "3️⃣ Bot avtomatik ravishda <b>vinetka24.uz/kod</b> havolasini va <b>QR-kod</b>ni taqdim etadi!"
    )
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.message(F.text == "📞 Biz bilan aloqa")
async def contact_us(message: Message):
    text = "📞 **Aloqa:** <code>972342424</code>\n🌐 **Veb-sayt:** vinetka24.uz"
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.message(F.text == "📸 Instagram (@vinetka24)")
async def instagram_page(message: Message):
    await message.answer(
        "📸 **Instagram:** [@vinetka24](https://instagram.com/vinetka24)",
        reply_markup=get_main_menu(),
        parse_mode="Markdown",
    )


@router.message(F.text == "📢 Telegram server (@vinetka24)")
async def telegram_channel(message: Message):
    await message.answer(
        "📢 **Telegram Server:** [@vinetka24](https://t.me/vinetka24)",
        reply_markup=get_main_menu(),
        parse_mode="Markdown",
    )


@router.message(F.text == "📁 Fayl yuborish")
async def start_files_mode(message: Message, state: FSMContext, bot: Bot):
    if not await check_user_access(message.from_user.id, bot):
        await state.clear()
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="📞 Telefon raqamni yuborish", request_contact=True
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            "❌ **Diqqat!** Raqamingiz kanal bazasidan topilmadi. Iltimos, raqamingizni qaytadan yuboring:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        await state.set_state(AlbumState.waiting_for_contact)
        return

    await state.set_state(AlbumState.waiting_for_files)
    await state.update_data(user_files=[], total_size=0)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Fayllarni yuborib bo'ldim (Tugatish)")],
            [KeyboardButton(text="❌ Bekor qilish")],
            [KeyboardButton(text="/start")],
        ],
        resize_keyboard=True,
    )
    await message.answer(
        "📤 **Fayl yuborish rejimi faollashdi.**\n\nFayllaringizni yuboring va tugatgach <b>'Tugatish'</b> tugmasini bosing.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_process(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Amal bekor qilindi.", reply_markup=get_main_menu())


@router.message(
    AlbumState.waiting_for_files,
    F.content_type.in_(
        {
            ContentType.PHOTO,
            ContentType.DOCUMENT,
            ContentType.VIDEO,
            ContentType.AUDIO,
        }
    ),
)
async def collect_files(message: Message, state: FSMContext):
    data = await state.get_data()
    files = data.get("user_files", [])
    total_size = data.get("total_size", 0)

    file_size = 0
    if message.document:
        file_size = message.document.file_size or 0
    elif message.video:
        file_size = message.video.file_size or 0
    elif message.audio:
        file_size = message.audio.file_size or 0
    elif message.photo:
        file_size = message.photo[-1].file_size or 0

    files.append(message.message_id)
    total_size += file_size

    await state.update_data(user_files=files, total_size=total_size)


@router.message(
    AlbumState.waiting_for_files, F.text == "✅ Fayllarni yuborib bo'ldim (Tugatish)"
)
async def finish_file_collection(message: Message, state: FSMContext, bot: Bot):
    if not await check_user_access(message.from_user.id, bot):
        await state.clear()
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(
                        text="📞 Telefon raqamni yuborish", request_contact=True
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            "❌ **Xatolik!** Raqamingiz kanal bazasidan topilmadi. Qaytadan ro'yxatdan o'ting:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        await state.set_state(AlbumState.waiting_for_contact)
        return

    data = await state.get_data()
    files = data.get("user_files", [])
    total_size = data.get("total_size", 0)

    if not files:
        await message.answer(
            "⚠️ Siz hali hech qanday fayl yubormadingiz! Iltimos, fayl yuboring."
        )
        return

    wait_msg = await message.answer(
        "⏳ Fayllar serverga yuklanmoqda va QR-kod tayyorlanmoqda...",
        reply_markup=ReplyKeyboardRemove(),
    )

    try:
        start_msg = await bot.send_message(
            chat_id=SERVER_ID,
            text="📥 [CORPORATE_START] Server tayyorlanmoqda...",
        )
        start_id = start_msg.message_id

        for msg_id in files:
            await bot.copy_message(
                chat_id=SERVER_ID,
                from_chat_id=message.from_user.id,
                message_id=msg_id,
            )

        end_msg = await bot.send_message(
            chat_id=SERVER_ID, text="🏁 [CORPORATE_END] Tugadi."
        )
        end_id = end_msg.message_id

        code_str = f"F{start_id}-{end_id}"
        auto_link = f"vinetka24.uz/{code_str}"

        try:
            await bot.edit_message_text(
                chat_id=SERVER_ID, message_id=start_id, text=code_str
            )
        except:
            pass

        try:
            await bot.edit_message_text(
                chat_id=SERVER_ID, message_id=end_id, text=f"https://{auto_link}"
            )
        except:
            pass

        try:
            await bot.delete_message(
                chat_id=message.chat.id, message_id=wait_msg.message_id
            )
        except:
            pass

        formatted_total_size = format_size(total_size)
        qr_bytes = generate_qr_code(f"https://{auto_link}")
        qr_photo = BufferedInputFile(qr_bytes, filename="vinetka_qr.png")

        await message.answer_photo(
            photo=qr_photo,
            caption=(
                "✅ **Fayllar muvaffaqiyatli joylandi!**\n\n"
                f"📊 Jami fayllar: {len(files)} ta\n"
                f"📦 Hajmi: {formatted_total_size}\n"
                f"🔑 Sizning kodingiz: <code>{code_str}</code>\n\n"
                f"🔗 {auto_link}"
            ),
            parse_mode="HTML",
            reply_markup=get_main_menu(),
        )

        await state.clear()

    except Exception as e:
        try:
            await bot.delete_message(
                chat_id=message.chat.id, message_id=wait_msg.message_id
            )
        except:
            pass
        await message.answer(
            f"⚠️ Xatolik yuz berdi: {e}", reply_markup=get_main_menu()
        )


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    
    # Eski postlarni o'qib chiqish uchun yordamchi funksiya chaqiruvi
    await scan_channel_history(bot)
    
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
