import asyncio
from datetime import datetime
import io
import json
import logging
import os
import re
import sqlite3
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BufferedInputFile,
    ContentType,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
import qrcode

# ================= CONFIGURATSIYA =================
# Kerakli Tokenlar va IDlar
TOKEN = (  # Asosiy bot tokeni (oxirgi koddan olindi)
    "8830593585:AAFbI3UwrgYNqYpK7tds9LYS-AsvKqjnNQA"
)
SERVER_ID = -1004423144311  # Fayllar saqlanadigan server kanal
ADS_CHANNEL_ID = -1004389076514  # Reklama kanali ID si
HELP_CHANNEL_ID = -1004302682261  # Qo'llanma kanali ID si
CHECK_CHANNEL_ID = -1003992475947  # Tekshiriladigan kanal ID si

DB_FILE = "limits.json"

logging.basicConfig(level=logging.INFO)
router = Router()

# Xotiradagi foydalanuvchilar bazasi (1-kod uchun)
DATABASE_USERS = set()

# SQLite bazasi (3-kod uchun)
db = sqlite3.connect("users.db")
cursor = db.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        phone TEXT,
        message_id INTEGER
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS allowed_posts (
        message_id INTEGER PRIMARY KEY,
        phone_digits TEXT
    )
""")
db.commit()


# FSM State lar
class LimitForm(StatesGroup):
  waiting_for_phone = State()
  waiting_for_date = State()
  waiting_for_time = State()


class AlbumState(StatesGroup):
  waiting_for_files = State()
  waiting_for_link = State()
  waiting_for_contact = State()


# ================= YORDAMCHI FUNKSIYALAR =================
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


def load_limits():
  if not os.path.exists(DB_FILE):
    return []
  try:
    with open(DB_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  except:
    return []


def save_limits(data):
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


def get_main_menu():
  return ReplyKeyboardMarkup(
      keyboard=[
          [KeyboardButton(text="📁 Fayl yuborish")],
          [KeyboardButton(text="📥 Fayllarni yuklab olish")],
          [
              KeyboardButton(text="📖 Botning ishlash tartibi"),
              KeyboardButton(text="📞 Biz bilan aloqa"),
          ],
          [
              KeyboardButton(text="📸 Instagram (@vinetka24)"),
              KeyboardButton(text="📢 Telegram server (@vinetka24)"),
          ],
          [
              KeyboardButton(text="⏳ Muddat qo'yish"),
              KeyboardButton(text="❌ Bekor qilish"),
          ],
          [KeyboardButton(text="/start")],
      ],
      resize_keyboard=True,
  )


# --- Kanaldagi pin qilingan xabarlarni olish ---
async def get_ad_message_id(bot: Bot) -> int:
  try:
    chat = await bot.get_chat(chat_id=ADS_CHANNEL_ID)
    if chat.pinned_message:
      return chat.pinned_message.message_id
  except Exception as e:
    logging.error(f"Reklama pin qilingan xabarni olishda xatolik: {e}")
  return 0


async def get_help_message_id(bot: Bot) -> int:
  try:
    chat = await bot.get_chat(chat_id=HELP_CHANNEL_ID)
    if chat.pinned_message:
      return chat.pinned_message.message_id
  except Exception as e:
    logging.error(f"Qo'llanma pin qilingan xabarni olishda xatolik: {e}")
  return 0


# --- KANAL POSTLARINI BAZAGA YOZISH ---
@router.channel_post()
async def channel_post_handler(message: Message):
  if message.chat.id == CHECK_CHANNEL_ID and message.text:
    digits = re.sub(r"\D", "", message.text)
    if len(digits) >= 9:
      last_9 = digits[-9:]
      cursor.execute(
          "INSERT OR REPLACE INTO allowed_posts (message_id, phone_digits)"
          " VALUES (?, ?)",
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
            "INSERT OR REPLACE INTO allowed_posts (message_id, phone_digits)"
            " VALUES (?, ?)",
            (message.message_id, last_9),
        )
      else:
        cursor.execute(
            "DELETE FROM allowed_posts WHERE message_id = ?",
            (message.message_id,),
        )
    else:
      cursor.execute(
          "DELETE FROM allowed_posts WHERE message_id = ?", (message.message_id,),
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
  phone, message_id = user_row
  try:
    msg = await bot.get_chat_message(
        chat_id=CHECK_CHANNEL_ID, message_id=message_id
    )
    if not msg.text:
      return False
    digits = re.sub(r"\D", "", msg.text)
    user_digits = re.sub(r"\D", "", phone)
    if (
        len(user_digits) >= 9
        and len(digits) >= 9
        and user_digits[-9:] != digits[-9:]
    ):
      return False
  except Exception:
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    db.commit()
    return False
  return True


# ================= ASOSIY BUYRUQLAR VA ROUTERLAR =================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
  await state.clear()
  user_id = message.from_user.id
  DATABASE_USERS.add(user_id)

  ad_msg_id = await get_ad_message_id(bot)
  if ad_msg_id > 0:
    try:
      await bot.copy_message(
          chat_id=user_id, from_chat_id=ADS_CHANNEL_ID, message_id=ad_msg_id
      )
      await asyncio.sleep(0.3)
    except:
      pass

  await message.answer(
      "🏛 <b>VINETKA24 — Boshqaruv Tizimi</b>\n\n"
      "Assalomu alaykum! Kerakli amalni tanlang.",
      reply_markup=get_main_menu(),
      parse_mode="HTML",
  )


# --- 1-QISM: Fayllarni yuklab olish (Kod bo'yicha) ---
@router.message(F.text == "📥 Fayllarni yuklab olish")
async def start_download_mode(message: Message):
  await message.answer(
      "📥 Kodni yuboring (Masalan: <code>F5-8</code>):",
      reply_markup=get_main_menu(),
      parse_mode="HTML",
  )


# --- 2-QISM: Muddat qo'yish tizimi ---
@router.message(Command("muddat"))
@router.message(F.text == "⏳ Muddat qo'yish")
async def start_limit(message: Message, state: FSMContext):
  await state.clear()
  await message.answer(
      "📱 *Mijozning telefon raqamini kiriting:*\n*(Namuna: `+998901234567`)*",
      reply_markup=get_main_menu(),
      parse_mode=ParseMode.MARKDOWN,
  )
  await state.set_state(LimitForm.waiting_for_phone)


@router.message(F.text == "❌ Bekor qilish")
async def cancel_process(message: Message, state: FSMContext):
  await state.clear()
  await message.answer("❌ *Amaliyot bekor qilindi.*", reply_markup=get_main_menu())


@router.message(LimitForm.waiting_for_phone)
async def process_phone_limit(message: Message, state: FSMContext):
  phone = message.text.strip()
  if not phone.startswith("+998") or len(phone) != 13:
    await message.answer(
        "❌ *Noto'g'ri format!*\nIltimos, raqamni quyidagi ko'rinishda kiriting:"
        " `+998XXXXXXXXX`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return
  await state.update_data(phone=phone)
  today_str = datetime.now().strftime("%d.%m.%Y")
  await message.answer(
      f"📅 *Sanani kiriting:*\n*(Namuna: `{today_str}`)*",
      parse_mode=ParseMode.MARKDOWN,
  )
  await state.set_state(LimitForm.waiting_for_date)


@router.message(LimitForm.waiting_for_date)
async def process_date_limit(message: Message, state: FSMContext):
  date_text = message.text.strip()
  try:
    datetime.strptime(date_text, "%d.%m.%Y")
  except ValueError:
    today_str = datetime.now().strftime("%d.%m.%Y")
    await message.answer(
        f"❌ *Noto'g'ri sana formati!*\nNamuna: `{today_str}`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return
  await state.update_data(date=date_text)
  now_time_str = datetime.now().strftime("%H:%M")
  await message.answer(
      f"⏰ *Soatni kiriting:*\n*(Namuna: `{now_time_str}`)*",
      parse_mode=ParseMode.MARKDOWN,
  )
  await state.set_state(LimitForm.waiting_for_time)


@router.message(LimitForm.waiting_for_time)
async def process_time_and_finish_limit(
    message: Message, state: FSMContext, bot: Bot
):
  time_text = message.text.strip()
  try:
    datetime.strptime(time_text, "%H:%M")
  except ValueError:
    now_time_str = datetime.now().strftime("%H:%M")
    await message.answer(
        f"❌ *Noto'g'ri soat formati!*\nNamuna: `{now_time_str}`",
        parse_mode=ParseMode.MARKDOWN,
    )
    return

  data = await state.get_data()
  phone = data.get("phone")
  date = data.get("date")
  operator_name = message.from_user.full_name
  target_dt = datetime.strptime(f"{date} {time_text}", "%d.%m.%Y %H:%M")
  target_timestamp = target_dt.timestamp()

  channel_text = (
      f"╔═══════════════════════╗\n"
      f"  🔒 *YANGI MUDDATLI CHEKLOV*\n"
      f"╚═══════════════════════╝\n\n"
      f"📱 *Mijoz raqami:* `{phone}`\n"
      f"📅 *Belgilangan muddat:* `{date} yil, {time_text}`\n"
      f"⚙️ *Holati:* `Faol` 🟢\n"
      f"👤 *Operator:* {operator_name}\n\n"
      f"─────────────────────────"
  )

  try:
    sent_msg = await bot.send_message(
        chat_id=CHECK_CHANNEL_ID, text=channel_text, parse_mode=ParseMode.MARKDOWN
    )
    limits = load_limits()
    limits.append({
        "message_id": sent_msg.message_id,
        "chat_id": CHECK_CHANNEL_ID,
        "phone": phone,
        "date": date,
        "time": time_text,
        "operator": operator_name,
        "target_timestamp": target_timestamp,
        "expired": False,
    })
    save_limits(limits)
    await message.answer(
        "✅ *Muvaffaqiyatli saqlandi va kanalga yuborildi!*",
        reply_markup=get_main_menu(),
        parse_mode=ParseMode.MARKDOWN,
    )
  except Exception as e:
    await message.answer(
        f"⚠️ *Xatolik yuz berdi:* `{e}`",
        reply_markup=get_main_menu(),
        parse_mode=ParseMode.MARKDOWN,
    )
  await state.clear()


# --- 3-QISM: Fayl yuborish va kontakt tekshiruvi ---
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
        "❌ **Diqqat!** Raqamingiz bazadan topilmadi yoki kanaldan o'chirilgan."
        " Iltimos, raqamingizni yuboring:",
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
      "📤 **Fayl yuborish rejimi faollashdi.**\n\nFayllaringizni yuboring va"
      " tugatgach <b>'Tugatish'</b> tugmasini bosing.",
      reply_markup=keyboard,
      parse_mode="HTML",
  )


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
        "INSERT OR REPLACE INTO users (user_id, phone, message_id) VALUES (?, ?,"
        " ?)",
        (message.from_user.id, phone, msg_id),
    )
    db.commit()
    await message.answer(
        "✅ **Tabriklaymiz! Raqamingiz tasdiqlandi.**",
        reply_markup=get_main_menu(),
        parse_mode="Markdown",
    )
    await state.clear()
  else:
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
        "❌ **Bu telefon raqam kanal bazasida topilmadi!** Qaytadan urinib"
        " ko'ring:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


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
  data = await state.get_data()
  files = data.get("user_files", [])
  total_size = data.get("total_size", 0)

  if not files:
    await message.answer("⚠️ Siz hali hech qanday fayl yubormadingiz!")
    return

  wait_msg = await message.answer(
      "⏳ Fayllar serverga yuklanmoqda...", reply_markup=ReplyKeyboardRemove()
  )
  try:
    start_msg = await bot.send_message(
        chat_id=SERVER_ID, text="📥 [CORPORATE_START_MARKER]"
    )
    start_id = start_msg.message_id

    for msg_id in files:
      await bot.copy_message(
          chat_id=SERVER_ID,
          from_chat_id=message.from_user.id,
          message_id=msg_id,
      )
      await asyncio.sleep(0.2)

    end_msg = await bot.send_message(
        chat_id=SERVER_ID, text="🏁 [CORPORATE_END_MARKER]"
    )
    end_id = end_msg.message_id
    code_str = f"F{start_id}-{end_id}"

    try:
      await bot.edit_message_text(
          chat_id=SERVER_ID, message_id=start_id, text=code_str
      )
    except:
      pass

    try:
      await bot.delete_message(
          chat_id=message.chat.id, message_id=wait_msg.message_id
      )
    except:
      pass

    await state.update_data(
        start_id=start_id, end_id=end_id, code_str=code_str, user_files=[]
    )
    await state.set_state(AlbumState.waiting_for_link)

    await message.answer(
        f"✅ <b>Sizning kodingiz:</b> <code>{code_str}</code>\n\n"
        f"🔗 Endi <b>vinetka24.uz</b> havolasini yuboring:",
        parse_mode="HTML",
    )
  except Exception as e:
    await message.answer(f"⚠️ Xatolik: {e}", reply_markup=get_main_menu())


@router.message(AlbumState.waiting_for_link, F.text)
async def check_user_link(message: Message, state: FSMContext, bot: Bot):
  text = message.text.strip()
  if text == "❌ Bekor qilish":
    await state.clear()
    await message.answer("❌ Amal bekor qilindi.", reply_markup=get_main_menu())
    return

  if "vinetka24.uz" not in text.lower():
    await message.answer(
        "❌ Havolada <b>vinetka24.uz</b> manzili topilmadi!", parse_mode="HTML"
    )
    return

  data = await state.get_data()
  end_id = data.get("end_id")
  code_str = data.get("code_str")

  try:
    try:
      await bot.edit_message_text(
          chat_id=SERVER_ID, message_id=end_id, text=text
      )
    except:
      pass

    qr_bytes = generate_qr_code(text)
    qr_photo = BufferedInputFile(qr_bytes, filename="vinetka_qr.png")
    await message.answer_photo(
        photo=qr_photo,
        caption=(
            f"🎉 **Tayyor!**\n🔗 Havola: {text}\n🔐 Kod:"
            f" <code>{code_str}</code>"
        ),
        parse_mode="HTML",
        reply_markup=get_main_menu(),
    )
    await state.clear()
  except Exception as e:
    await message.answer(f"⚠️ Xatolik: {e}", reply_markup=get_main_menu())


# --- Matnli kodlar orqali fayl qidirish va yuborish (1-bot mantig'i) ---
@router.message(F.text)
async def process_code_or_link(message: Message, bot: Bot):
  text = message.text.strip()
  if text in [
      "📥 Fayllarni yuklab olish",
      "📖 Qo'llanma",
      "/start",
      "📁 Fayl yuborish",
      "⏳ Muddat qo'yish",
      "❌ Bekor qilish",
  ]:
    return

  match = re.search(r"f\s*([0-9]+)\s*-\s*([0-9]+)", text, re.IGNORECASE)
  if not match:
    return

  start_id = int(match.group(1))
  end_id = int(match.group(2))
  if start_id > end_id:
    start_id, end_id = end_id, start_id

  await message.answer(
      "🔍 Parol va xabar ID lari tekshirilmoqda...",
      reply_markup=ReplyKeyboardRemove(),
  )
  cleaned_input_code = text.replace(" ", "").upper()
  code_verified = False

  try:
    for check_id in [start_id, end_id]:
      try:
        test_msg = await bot.copy_message(
            chat_id=message.from_user.id,
            from_chat_id=SERVER_ID,
            message_id=check_id,
        )
        msg_text = test_msg.text or test_msg.caption or ""
        await test_msg.delete()
        if cleaned_input_code in msg_text.replace(" ", "").upper():
          code_verified = True
          break
      except:
        continue
  except Exception as e:
    logging.error(f"ID tekshirishda xatolik: {e}")

  if not code_verified:
    await message.answer(
        "❌ Xatolik: Ko'rsatilgan ID larda bu parol mavjud emas yoki noto'g'ri!",
        reply_markup=get_main_menu(),
    )
    return

  await message.answer(
      "⏳ Tasdiqlandi, videolar va fayllar yuborilmoqda...",
      reply_markup=ReplyKeyboardRemove(),
  )
  sent_count = 0
  try:
    for msg_id in range(start_id + 1, end_id):
      try:
        await bot.copy_message(
            chat_id=message.from_user.id,
            from_chat_id=SERVER_ID,
            message_id=msg_id,
        )
        sent_count += 1
        await asyncio.sleep(0.3)
      except:
        continue

    if sent_count > 0:
      await message.answer(
          f"✅ Jami {sent_count} ta fayl/video muvaffaqiyatli yuborildi!",
          reply_markup=get_main_menu(),
      )
    else:
      await message.answer(
          "⚠️ Ko'rsatilgan oraliqda videolar yoki fayllar topilmadi.",
          reply_markup=get_main_menu(),
      )
  except Exception as e:
    await message.answer(
        f"⚠️ Xatolik yuz berdi: {e}", reply_markup=get_main_menu()
    )


# --- Qo'shimcha menyu tugmalari ---
@router.message(F.text == "📖 Botning ishlash tartibi")
async def help_instruction(message: Message):
  text = (
      "📋 **VINETKA24 — Botdan Foydalanish Tartibi:**\n\n"
      "1️⃣ <b>'📁 Fayl yuborish'</b> tugmasini bosing.\n"
      "2️⃣ Fayllaringizni yuboring va <b>'Tugatish'</b> ni bosing.\n"
      "3️⃣ Chiqqan <b>kodni</b> oling va sayt havolasini yuboring."
  )
  await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.message(F.text == "📞 Biz bilan aloqa")
async def contact_us(message: Message):
  await message.answer(
      "📞 **Aloqa:** <code>972342424</code>\n🌐 **Veb-sayt:** vinetka24.uz",
      reply_markup=get_main_menu(),
      parse_mode="HTML",
  )


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


# --- Fon vazifalari (Background Tasks) ---
async def check_expirations(bot: Bot):
  while True:
    try:
      limits = load_limits()
      now_timestamp = datetime.now().timestamp()
      updated = False
      for item in limits:
        if not item["expired"] and now_timestamp >= item["target_timestamp"]:
          expired_text = (
              f"╔═══════════════════════╗\n"
              f"  🔒 *YANGI MUDDATLI CHEKLOV*\n"
              f"╚═══════════════════════╝\n\n"
              f"📱 *Mijoz raqami:* `{item['phone']}`\n"
              f"📅 *Belgilangan muddat:* `{item['date']} yil,"
              f" {item['time']}`\n"
              f"⚙️ *Holati:* `Muddati tugagan` 🔴\n"
              f"👤 *Operator:* {item['operator']}\n\n"
              f"─────────────────────────"
          )
          try:
            await bot.edit_message_text(
                chat_id=item["chat_id"],
                message_id=item["message_id"],
                text=expired_text,
                parse_mode=ParseMode.MARKDOWN,
            )
          except Exception as e:
            logging.error(f"Xabarni tahrirlashda xatolik: {e}")
          item["expired"] = True
          updated = True
      if updated:
        save_limits(limits)
    except Exception as e:
      logging.error(f"Background task xatoligi: {e}")
    await asyncio.sleep(30)


# ================= ASOSIY FUNKSIYA =================
async def main():
  bot = Bot(token=TOKEN)
  dp = Dispatcher(storage=MemoryStorage())
  dp.include_router(router)

  await bot.delete_webhook(drop_pending_updates=True)

  # Muddatlarni tekshiruvchi background taskni ishga tushirish
  asyncio.create_task(check_expirations(bot))

  print("Birlashtirilgan bot muvaffaqiyatli ishga tushdi va tayyor!")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())