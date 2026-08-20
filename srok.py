import asyncio
from datetime import datetime
import json
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

# Bot tokeni va kanal ID raqami
TOKEN = "8946621974:AAGF2jCmKvh92jMarRbpA0T2jDRixjfm5TQ"
CHANNEL_ID = -1003992475947

DB_FILE = "limits.json"

logging.basicConfig(level=logging.INFO)
router = Router()


class LimitForm(StatesGroup):
  waiting_for_phone = State()
  waiting_for_date = State()
  waiting_for_time = State()


# --- JSON BAZA BILAN ISHLASH ---
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


# --- PASTDAGI ASOSIY MENYU TUGMALARI ---
def get_reply_keyboard():
  return ReplyKeyboardMarkup(
      keyboard=[
          [
              KeyboardButton(text="⏳ Muddat qo'yish"),
              KeyboardButton(text="❌ Bekor qilish"),
          ]
      ],
      resize_keyboard=True,
  )


# --- BOT BUYRUQLARI ---
async def set_bot_commands(bot: Bot):
  commands = [
      BotCommand(command="start", description="Botni ishga tushirish"),
      BotCommand(command="muddat", description="⏳ Muddat qo'yish"),
  ]
  await bot.set_my_commands(commands)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
  await state.clear()
  await message.answer(
      "👋 *Assalomu alaykum!*\nMijozlarga cheklov muddatini o'rnatish botiga"
      " xush kelibsiz.\n\nPastdagi tugmalar yordamida amalni bajaring:",
      reply_markup=get_reply_keyboard(),
      parse_mode=ParseMode.MARKDOWN,
  )


@router.message(Command("muddat"))
@router.message(F.text == "⏳ Muddat qo'yish")
async def start_limit(message: Message, state: FSMContext):
  await state.clear()
  await message.answer(
      "📱 *Mijozning telefon raqamini kiriting:*\n*(Namuna: `+998901234567`)*",
      reply_markup=get_reply_keyboard(),
      parse_mode=ParseMode.MARKDOWN,
  )
  await state.set_state(LimitForm.waiting_for_phone)


@router.message(F.text == "❌ Bekor qilish")
async def cancel_process(message: Message, state: FSMContext):
  await state.clear()
  await message.answer(
      "❌ *Amaliyot bekor qilindi.*",
      reply_markup=get_reply_keyboard(),
      parse_mode=ParseMode.MARKDOWN,
  )


# --- 1. RAQAMNI QABUL QILISH ---
@router.message(LimitForm.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
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


# --- 2. SANANI QABUL QILISH ---
@router.message(LimitForm.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
  date_text = message.text.strip()
  try:
    datetime.strptime(date_text, "%d.%m.%Y")
  except ValueError:
    today_str = datetime.now().strftime("%d.%m.%Y")
    await message.answer(
        f"❌ *Noto'g'ri sana formati!*\nIltimos, sanani to'g'ri kiriting (Namuna:"
        f" `{today_str}`)",
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


# --- 3. SOATni QABUL QILISH VA KANALGA YUBORISH ---
@router.message(LimitForm.waiting_for_time)
async def process_time_and_finish(message: Message, state: FSMContext, bot: Bot):
  time_text = message.text.strip()
  try:
    datetime.strptime(time_text, "%H:%M")
  except ValueError:
    now_time_str = datetime.now().strftime("%H:%M")
    await message.answer(
        f"❌ *Noto'g'ri soat formati!*\nIltimos, soatni to'g'ri kiriting (Namuna:"
        f" `{now_time_str}`)",
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
        chat_id=CHANNEL_ID, text=channel_text, parse_mode=ParseMode.MARKDOWN
    )

    limits = load_limits()
    limits.append({
        "message_id": sent_msg.message_id,
        "chat_id": CHANNEL_ID,
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
        reply_markup=get_reply_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
  except Exception as e:
    await message.answer(
        f"⚠️ *Xatolik yuz berdi:* `{e}`",
        reply_markup=get_reply_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )

  await state.clear()


# --- ISHGA TUSHGANDA TEKSHIRISH ---
async def startup_check(bot: Bot):
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
        item["expired"] = True
        updated = True
      except Exception as e:
        logging.error(f"Eski xabarni tahrirlashda xatolik: {e}")

  if updated:
    save_limits(limits)


# --- ORQA FONDA TEKSHIRIB TURISH ---
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


# --- BOTNI ISHGA TUSHIRISH ---
async def main():
  bot = Bot(token=TOKEN)
  dp = Dispatcher(storage=MemoryStorage())
  dp.include_router(router)

  await set_bot_commands(bot)
  await bot.delete_webhook(drop_pending_updates=True)

  await startup_check(bot)
  asyncio.create_task(check_expirations(bot))

  print("Bot ishga tushdi...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())