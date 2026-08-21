import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

# Token va Kanal ID lari
TOKEN = "8388203169:AAGdK7qJvdSOgEpBuDjLNVjwGWqgxcq1A-0"
SERVER_ID = -1004423144311  # Fayllar saqlanadigan server kanal[cite: 1]
ADS_CHANNEL_ID = -1004389076514  # Reklama kanali ID si[cite: 1]
HELP_CHANNEL_ID = -1004302682261  # Qo'llanma kanali ID si[cite: 1]

logging.basicConfig(level=logging.INFO)
router = Router()

# Foydalanuvchilar bazasi (xotirada saqlanadi)[cite: 1]
DATABASE_USERS = set()


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Fayllarni yuklab olish")],
            [KeyboardButton(text="📖 Qo'llanma")],
            [KeyboardButton(text="/start")],
        ],
        resize_keyboard=True,
    )


# Kanaldagi pin (mahkamlangan) qilingan reklama postining ID raqamini avtomatik olish[cite: 1]
async def get_ad_message_id(bot: Bot) -> int:
    try:
        chat = await bot.get_chat(chat_id=ADS_CHANNEL_ID)
        if chat.pinned_message:
            return chat.pinned_message.message_id
    except Exception as e:
        logging.error(f"Reklama pin qilingan xabarni olishda xatolik: {e}")
    return 0


# Qo'llanma kanalidagi pin (mahkamlangan) qilingan postning ID raqamini avtomatik olish[cite: 1]
async def get_help_message_id(bot: Bot) -> int:
    try:
        chat = await bot.get_chat(chat_id=HELP_CHANNEL_ID)
        if chat.pinned_message:
            return chat.pinned_message.message_id
    except Exception as e:
        logging.error(f"Qo'llanma pin qilingan xabarni olishda xatolik: {e}")
    return 0


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    DATABASE_USERS.add(user_id)

    ad_msg_id = await get_ad_message_id(bot)
    if ad_msg_id > 0:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=ADS_CHANNEL_ID,
                message_id=ad_msg_id,
            )
            await asyncio.sleep(0.3)
        except Exception as e:
            logging.error(f"Reklama yuborishda xatolik: {e}")

    await message.answer(
        "🏛 <b>VINETKA24 — Serverdan Fayl Qabul Qilish Boti</b>\n\n"
        "Assalomu alaykum!\n"
        "Kerakli kodni yuboring (Masalan: <code>F5-8</code>).",
        reply_markup=get_main_menu(),
        parse_mode="HTML",
    )


@router.message(F.text == "📖 Qo'llanma")
async def help_instruction(message: Message, bot: Bot):
    help_msg_id = await get_help_message_id(bot)
    if help_msg_id > 0:
        try:
            await bot.copy_message(
                chat_id=message.from_user.id,
                from_chat_id=HELP_CHANNEL_ID,
                message_id=help_msg_id,
            )
        except Exception as e:
            await message.answer(
                "⚠️ Qo'llanma xabarini yuborishda xatolik yuz berdi.",
                reply_markup=get_main_menu(),
            )
            logging.error(f"Qo'llanma yuborishda xatolik: {e}")
    else:
        await message.answer(
            "⚠️ Qo'llanma kanalida pin qilingan post topilmadi.",
            reply_markup=get_main_menu(),
        )


@router.message(F.text == "📥 Fayllarni yuklab olish")
async def start_download_mode(message: Message):
    await message.answer(
        "📥 Kodni yuboring (Masalan: <code>F5-8</code>):",
        reply_markup=get_main_menu(),
        parse_mode="HTML",
    )


# Barcha matnli xabarlarni tekshirib, kodni qidiradi[cite: 1]
@router.message(F.text)
async def process_code_or_link(message: Message, bot: Bot):
    user_id = message.from_user.id
    is_new = user_id not in DATABASE_USERS
    DATABASE_USERS.add(user_id)

    if is_new:
        ad_msg_id = await get_ad_message_id(bot)
        if ad_msg_id > 0:
            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=ADS_CHANNEL_ID,
                    message_id=ad_msg_id,
                )
                await asyncio.sleep(0.3)
            except Exception:
                pass

    text = message.text.strip()

    if text in ["📥 Fayllarni yuklab olish", "📖 Qo'llanma", "/start"]:
        return

    # Havola yoki F... formatini to'g'ri o'qish uchun regex
    match = re.search(r"f\s*([0-9]+)\s*-\s*([0-9]+)", text, re.IGNORECASE)

    if not match:
        await message.answer(
            "❌ Kod formati noto'g'ri! Masalan: <code>F5-8</code> ko'rinishida yuboring.",
            parse_mode="HTML",
        )
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
    # Agar foydalanuvchi faqat F106-108 yuborsa, uni vinetka24.uz/F106-108 formatiga moslaymiz
    if not cleaned_input_code.startswith("VINETKA24.UZ/"):
        short_code = cleaned_input_code
    else:
        short_code = cleaned_input_code.split("/")[-1]

    code_verified = False

    try:
        # Serverdagi start_id va end_id xabarlarini tekshiramiz
        for check_id in [start_id, end_id]:
            try:
                test_msg = await bot.copy_message(
                    chat_id=message.from_user.id,
                    from_chat_id=SERVER_ID,
                    message_id=check_id,
                )
                msg_text = test_msg.text or test_msg.caption or ""
                await test_msg.delete()

                print(f"Serverdan o'qilgan matn (ID {check_id}): {msg_text}")

                # Tekshiruvni yanada moslashuvchan qilamiz
                normalized_msg_text = msg_text.replace(" ", "").upper()
                if short_code in normalized_msg_text or cleaned_input_code in normalized_msg_text:
                    code_verified = True
                    break
            except Exception as err:
                logging.warning(f"ID {check_id} ni tekshirishda xatolik: {err}")
                continue
    except Exception as e:
        logging.error(f"ID tekshirishda umumiy xatolik: {e}")

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
            except Exception:
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


@router.channel_post(F.chat.id == ADS_CHANNEL_ID)
async def broadcast_ads(message: Message, bot: Bot):
    if not DATABASE_USERS:
        return
    for user_id in list(DATABASE_USERS):
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=ADS_CHANNEL_ID,
                message_id=message.message_id,
            )
            await asyncio.sleep(0.2)
        except Exception:
            pass


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot muvaffaqiyatli ishga tushdi va tayyor!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
