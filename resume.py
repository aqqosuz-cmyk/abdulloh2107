import os
import shutil
import asyncio
import logging
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches
from PIL import Image, ImageDraw, ImageFont

API_TOKEN = "8678566738:AAE4UmWPxycyRC7IOHQ3GCCP9mnCCOIb7Rk"

# QO'LDA TO'LOVNI TASDIQLASH
ADMIN_ID = 7737099509
PAYMENT_CARD = "6262570240174476"
CARD_OWNER = "Ergashev Tohirjon"
PAYMENT_AMOUNT = "30 000 so'm"
SUPPORT_PHONE = "908909199"
pending_payments = {}

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "shablon.docx")

class Form(StatesGroup):
    fish = State()
    t_yil = State()
    t_joy = State()
    millati = State()
    malumoti = State()
    oquv_joyi = State()
    mutaxassislik = State()
    ilmiy_daraja = State()
    ilmiy_unvon = State()
    chet_tillari = State()
    mukofotlar = State()
    deputat = State()
     
    # Mehnat faoliyati
    mehnat_joyi = State()
    mehnat_lavozimi = State()
    mehnat_kirgan = State()
    mehnat_bosha = State()
     
    # Qarindoshlar
    q_qarindoshlik = State()
    q_fio = State()
    q_yil_joy = State()
    q_ish = State()
    q_turar = State()
     
    # Rasm
    photo = State()
    payment_receipt = State()

user_data_cache = {}

def start_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="START")]],
        resize_keyboard=True,
        is_persistent=True
    )

def no_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="YO'Q")]],
        resize_keyboard=True
    )

def answer_value(message: Message):
    if (message.text or "").strip().upper() in {"YO'Q", "YO‘Q", "YOQ"}:
        return "Yo'q"
    return message.text or ""

async def start_form(message: Message, state: FSMContext):
    await state.clear()
    user_data_cache[message.from_user.id] = {"mehnat": [], "qarindoshlar": []}
    await message.answer(
        "Assalomu alaykum! Ma'lumotnoma tuzishni boshlaymiz.\n\n"
        "To'liq FIO (Familiya Ism Sharifingiz) kiriting:",
        reply_markup=no_keyboard()
    )
    await state.set_state(Form.fish)

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await start_form(message, state)

@dp.message(F.text == "START")
async def start_button(message: Message, state: FSMContext):
    await start_form(message, state)

@dp.message(Form.fish)
async def process_fish(message: Message, state: FSMContext):
    fish = answer_value(message)
    if fish != "Yo'q":
        fish = fish.upper()
    await state.update_data(fish=fish)
    await message.answer("Tug'ilgan yilingizni kiriting (masalan: 13.05.2000-yil):", reply_markup=no_keyboard())
    await state.set_state(Form.t_yil)

@dp.message(Form.t_yil)
async def process_t_yil(message: Message, state: FSMContext):
    await state.update_data(t_yil=answer_value(message))
    await message.answer("Tug'ilgan joyingizni kiriting (viloyat, tuman):", reply_markup=no_keyboard())
    await state.set_state(Form.t_joy)

@dp.message(Form.t_joy)
async def process_t_joy(message: Message, state: FSMContext):
    await state.update_data(t_joy=answer_value(message))
    await message.answer("Millatingizni kiriting:", reply_markup=no_keyboard())
    await state.set_state(Form.millati)

@dp.message(Form.millati)
async def process_millati(message: Message, state: FSMContext):
    await state.update_data(millati=answer_value(message))
    await message.answer("Ma'lumotingizni kiriting (Oliy, o'rta-maxsus va h.k.):", reply_markup=no_keyboard())
    await state.set_state(Form.malumoti)

@dp.message(Form.malumoti)
async def process_malumoti(message: Message, state: FSMContext):
    await state.update_data(malumoti=answer_value(message))
    await message.answer("Ta'lim muassasasini (universitet/maktab nomi) kiriting:", reply_markup=no_keyboard())
    await state.set_state(Form.oquv_joyi)

@dp.message(Form.oquv_joyi)
async def process_oquv_joyi(message: Message, state: FSMContext):
    await state.update_data(oquv_joyi=answer_value(message))
    await message.answer("Mutaxassisligingizni kiriting:", reply_markup=no_keyboard())
    await state.set_state(Form.mutaxassislik)

@dp.message(Form.mutaxassislik)
async def process_mutaxassislik(message: Message, state: FSMContext):
    await state.update_data(mutaxassislik=answer_value(message))
    await message.answer("Ilmiy darajangiz bormi? (Yo'q bo'lsa 'yo'q' deb yozing):", reply_markup=no_keyboard())
    await state.set_state(Form.ilmiy_daraja)

@dp.message(Form.ilmiy_daraja)
async def process_ilmiy_daraja(message: Message, state: FSMContext):
    await state.update_data(ilmiy_daraja=answer_value(message))
    await message.answer("Ilmiy unvoningiz bormi? (Yo'q bo'lsa 'yo'q' deb yozing):", reply_markup=no_keyboard())
    await state.set_state(Form.ilmiy_unvon)

@dp.message(Form.ilmiy_unvon)
async def process_ilmiy_unvon(message: Message, state: FSMContext):
    await state.update_data(ilmiy_unvon=answer_value(message))
    await message.answer("Qaysi chet tillarini bilasiz?", reply_markup=no_keyboard())
    await state.set_state(Form.chet_tillari)

@dp.message(Form.chet_tillari)
async def process_chet_tillari(message: Message, state: FSMContext):
    await state.update_data(chet_tillari=answer_value(message))
    await message.answer("Davlat mukofotlari bilan taqdirlanganmisiz? (Qanaqa / Yo'q):", reply_markup=no_keyboard())
    await state.set_state(Form.mukofotlar)

@dp.message(Form.mukofotlar)
async def process_mukofotlar(message: Message, state: FSMContext):
    await state.update_data(mukofotlar=answer_value(message))
    await message.answer("Xalq deputatlari Kengashi deputatimisiz yoki boshqa saylanadigan organ a'zosi? (To'liq yozing):", reply_markup=no_keyboard())
    await state.set_state(Form.deputat)

@dp.message(Form.deputat)
async def process_deputat(message: Message, state: FSMContext):
    await state.update_data(deputat=answer_value(message))
    await message.answer(
        "Endi **MEHNAT FAOLIYATI**ni kiritamiz.\n\n"
        "Ish joyining nomini kiriting:",
        reply_markup=no_keyboard()
    )
    await state.set_state(Form.mehnat_joyi)

@dp.message(Form.mehnat_joyi)
async def process_mehnat_joyi(message: Message, state: FSMContext):
    if (message.text or "").strip().upper() in {"YO'Q", "YO‘Q", "YOQ"}:
        uid = message.from_user.id
        user_data_cache[uid]["mehnat"] = []
        await message.answer(
            "Mehnat faoliyati kiritilmadi. Endi **YAQIN QARINDOSHLARI HAQIDA MA'LUMOT**ni kiritamiz.\n\n"
            "Qarindoshlik darajasini kiriting (masalan: Otasi, Onasi...):",
            reply_markup=no_keyboard()
        )
        await state.set_state(Form.q_qarindoshlik)
        return

    await state.update_data(m_joyi=answer_value(message))
    await message.answer("Lavozimi / kasbi:", reply_markup=no_keyboard())
    await state.set_state(Form.mehnat_lavozimi)

@dp.message(Form.mehnat_lavozimi)
async def process_mehnat_lavozimi(message: Message, state: FSMContext):
    await state.update_data(m_lavozimi=answer_value(message))
    await message.answer("Ishga kirgan yili (oy va yil):", reply_markup=no_keyboard())
    await state.set_state(Form.mehnat_kirgan)

@dp.message(Form.mehnat_kirgan)
async def process_mehnat_kirgan(message: Message, state: FSMContext):
    await state.update_data(m_kirgan=answer_value(message))
    await message.answer("Ishdan bo'shagan yili (hali ishlasa 'Hozirgacha' deb yozing):", reply_markup=no_keyboard())
    await state.set_state(Form.mehnat_bosha)

@dp.message(Form.mehnat_bosha)
async def process_mehnat_bosha(message: Message, state: FSMContext):
    data = await state.get_data()
    uid = message.from_user.id
     
    user_data_cache[uid]["mehnat"].append({
        'joyi': data.get('m_joyi'),
        'lavozimi': data.get('m_lavozimi'),
        'kirgan_yili': data.get('m_kirgan'),
        'bosha_yili': answer_value(message)
    })
     
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yana ish joyi qo'shish", callback_data="add_more_mehnat")],
        [InlineKeyboardButton(text="➡️ Qarindoshlarni kiritishga o'tish", callback_data="go_to_qarindosh")]
    ])
    await message.answer("Mehnat faoliyati saqlandi. Keyingi amalni tanlang:", reply_markup=kb)

@dp.callback_query(F.data == "add_more_mehnat")
async def add_more_mehnat_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Keyingi ish joyining nomini kiriting:")
    await state.set_state(Form.mehnat_joyi)
    await callback.answer()

@dp.callback_query(F.data == "go_to_qarindosh")
async def go_to_qarindosh_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Endi **YAQIN QARINDOSHLARI HAQIDA MA'LUMOT**ni kiritamiz.\n\n"
        "Qarindoshlik darajasini kiriting (masalan: Otasi, Onasi...):",
        reply_markup=no_keyboard()
    )
    await state.set_state(Form.q_qarindoshlik)
    await callback.answer()

@dp.message(Form.q_qarindoshlik)
async def process_q_qarindoshlik(message: Message, state: FSMContext):
    if (message.text or "").strip().upper() in {"YO'Q", "YO‘Q", "YOQ"}:
        uid = message.from_user.id
        user_data_cache[uid]["qarindoshlar"] = []
        await message.answer(
            "Yaqin qarindoshlar kiritilmadi. Endi **3x4 formatdagi shaxsiy rasmingizni** yuboring:",
            reply_markup=start_keyboard()
        )
        await state.set_state(Form.photo)
        return

    await state.update_data(q_daraja=answer_value(message))
    await message.answer("Qarindoshning FIO (Familiyasi, ismi va otasining ismi):", reply_markup=no_keyboard())
    await state.set_state(Form.q_fio)

@dp.message(Form.q_fio)
async def process_q_fio(message: Message, state: FSMContext):
    await state.update_data(q_fio=answer_value(message))
    await message.answer("Tug'ilgan yili va joyi:", reply_markup=no_keyboard())
    await state.set_state(Form.q_yil_joy)

@dp.message(Form.q_yil_joy)
async def process_q_yil_joy(message: Message, state: FSMContext):
    await state.update_data(q_yil_joy=answer_value(message))
    await message.answer("Ish joyi va lavozimi:", reply_markup=no_keyboard())
    await state.set_state(Form.q_ish)

@dp.message(Form.q_ish)
async def process_q_ish(message: Message, state: FSMContext):
    await state.update_data(q_ish=answer_value(message))
    await message.answer("Turar joyi:", reply_markup=no_keyboard())
    await state.set_state(Form.q_turar)

@dp.message(Form.q_turar)
async def process_q_turar(message: Message, state: FSMContext):
    data = await state.get_data()
    uid = message.from_user.id
     
    user_data_cache[uid]["qarindoshlar"].append({
        'qarindoshlik': data.get('q_daraja'),
        'fio': (data.get('q_fio') or 'Yo\'q').upper() if data.get('q_fio') != "Yo'q" else "Yo'q",
        'yil_joy': data.get('q_yil_joy'),
        'ish': data.get('q_ish'),
        'turar': answer_value(message)
    })
     
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yana qarindosh qo'shish", callback_data="add_more_q")],
        [InlineKeyboardButton(text="📷 Rasmni yuborishga o'tish", callback_data="go_to_photo")]
    ])
    await message.answer("Qarindosh saqlandi. Keyingi amalni tanlang:", reply_markup=kb)

@dp.callback_query(F.data == "add_more_q")
async def add_more_q_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Keyingi qarindoshning qarindoshlik darajasini kiriting:")
    await state.set_state(Form.q_qarindoshlik)
    await callback.answer()

@dp.callback_query(F.data == "go_to_photo")
async def go_to_photo_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Endi **3x4 formatdagi shaxsiy rasmingizni** yuboring:")
    await state.set_state(Form.photo)
    await callback.answer()

def create_preview_document_image(photo_path, data, uid):
    """A4 sahifa shaklida hujjat skrinshoti ko'rinishini yasab, ustiga NAMUNA yozadigan funksiya"""
    preview_dir = os.path.join("downloads", f"preview_{uid}")
    os.makedirs(preview_dir, exist_ok=True)
    png_path = os.path.join(preview_dir, "namuna_doc.png")

    # A4 proporsiyasidagi oq sahifa yaratamiz (masalan, kengligi 1240, balandligi 1754 - A4 300 DPI)
    width, height = 1240, 1754
    page = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(page)

    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_text = ImageFont.truetype("arial.ttf", 24)
        font_bold = ImageFont.truetype("arial.ttf", 26)
    except:
        font_title = font_text = font_bold = ImageFont.load_default()

    # 1. Hujjat sarlavhasi
    draw.text((width // 2, 100), "MA'LUMOTNOMA", fill=(0, 0, 0), font=font_title, anchor="mm")

    # 2. Shaxsiy rasmni o'ng yuqori burchakka qo'yish
    try:
        user_img = Image.open(photo_path).convert("RGB")
        # 3x4 proporsiyada kichraytiramiz
        user_img = user_img.resize((220, 293))
        page.paste(user_img, (width - 300, 180))
        # Rasm atrofiga ramka
        draw.rectangle([width - 300, 180, width - 80, 473], outline=(0, 0, 0), width=2)
    except:
        pass

    # 3. Asosiy matn ma'lumotlarini yozib chiqish
    fields = [
        ("F.I.O.:", data.get("fish", "")),
        ("Tug'ilgan yili:", data.get("t_yil", "")),
        ("Tug'ilgan joyi:", data.get("t_joy", "")),
        ("Millati:", data.get("millati", "")),
        ("Ma'lumoti:", data.get("malumoti", "")),
        ("Tamomlagan:", data.get("oquv_joyi", "")),
        ("Mutaxassisligi:", data.get("mutaxassislik", "")),
        ("Ilmiy darajasi:", data.get("ilmiy_daraja", "")),
        ("Chet tillari:", data.get("chet_tillari", ""))
    ]

    y = 200
    for label, val in fields:
        draw.text((100, y), f"{label} {val}", fill=(0, 0, 0), font=font_text)
        y += 50

    # Mehnat faoliyati sarlavhasi
    y += 30
    draw.text((100, y), "MEHNAT FAOLIYATI:", fill=(0, 0, 0), font=font_bold)
    y += 45

    mehnat_list = user_data_cache.get(uid, {}).get("mehnat", [])
    if mehnat_list:
        for m in mehnat_list[:3]: # Sig'ishigacha ko'rsatamiz
            text_m = f"• {m.get('kirgan_yili')} - {m.get('bosha_yili')}: {m.get('joyi')}, {m.get('lavozimi')}"
            draw.text((120, y), text_m, fill=(50, 50, 50), font=font_text)
            y += 40
    else:
        draw.text((120, y), "Ma'lumot kiritilmagan", fill=(100, 100, 100), font=font_text)
        y += 40

    # 4. Diagonal "NAMUNA" yozuvini sahifa ustiga bosish
    txt_layer = Image.new("RGBA", page.size, (255, 255, 255, 0))
    d_txt = ImageDraw.Draw(txt_layer)
    
    try:
        font_watermark = ImageFont.truetype("arial.ttf", 180)
    except:
        font_watermark = ImageFont.load_default()

    wt_text = "NAMUNA"
    # Katta shaffof matn yaratamiz
    w_bbox = d_txt.textbbox((0, 0), wt_text, font=font_watermark)
    ww, wh = w_bbox[2] - w_bbox[0], w_bbox[3] - w_bbox[1]
    
    watermark_img = Image.new("RGBA", (ww + 100, wh + 100), (255, 255, 255, 0))
    wd_draw = ImageDraw.Draw(watermark_img)
    wd_draw.text((50, 50), wt_text, font=font_watermark, fill=(180, 180, 180, 110)) # shaffof kulrang
    
    # Burchak ostida aylantiramiz
    watermark_img = watermark_img.rotate(35, expand=True, resample=Image.Resampling.BICUBIC)

    # Sahifa markaziga joylaymiz
    wx = (page.width - watermark_img.width) // 2
    wy = (page.height - watermark_img.height) // 2
    txt_layer.paste(watermark_img, (wx, wy), watermark_img)

    # Rasm va qatlamni birlashtiramiz
    final_page = Image.alpha_composite(page.convert("RGBA"), txt_layer).convert("RGB")
    final_page.save(png_path, format="PNG")

    return [png_path], preview_dir

@dp.message(Form.photo, F.photo | F.document)
async def process_photo(message: Message, state: FSMContext):
    os.makedirs("downloads", exist_ok=True)
    uid = message.from_user.id
    photo_path = f"downloads/photo_{uid}.jpg"

    if message.photo:
        file_info = await bot.get_file(message.photo[-1].file_id)
        await bot.download_file(file_info.file_path, destination=photo_path)
    elif message.document:
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, destination=photo_path)

    await message.answer("⏳ Hujjatingiz tayyorlanmoqda, biroz kuting...")
    data = await state.get_data()

    doc = DocxTemplate(TEMPLATE_PATH)
    img = InlineImage(doc, photo_path, width=Inches(1.1))
    context = {
        "fish": data.get("fish"),
        "t_yil": data.get("t_yil"),
        "t_joy": data.get("t_joy"),
        "millati": data.get("millati"),
        "malumoti": data.get("malumoti"),
        "oquv_joyi": data.get("oquv_joyi"),
        "mutaxassislik": data.get("mutaxassislik"),
        "ilmiy_daraja": data.get("ilmiy_daraja"),
        "ilmiy_unvon": data.get("ilmiy_unvon"),
        "chet_tillari": data.get("chet_tillari"),
        "mukofotlar": data.get("mukofotlar"),
        "deputat": data.get("deputat"),
        "mehnat": user_data_cache.get(uid, {}).get("mehnat", []),
        "qarindoshlar": user_data_cache.get(uid, {}).get("qarindoshlar", []),
        "rasm": img,
        "imzo": data.get("fish"),
        "sana": datetime.now().strftime("%d.%m.%Y"),
    }
    doc.render(context)

    person_name = (data.get("fish") or f"Malumotnoma_{uid}").strip()
    safe_name = re.sub(r'[<>:"/\\|?*]', "", person_name)
    file_path = os.path.join("downloads", f"{safe_name}.docx")
    doc.save(file_path)

    try:
        preview_paths, preview_dir = create_preview_document_image(photo_path, data, uid)
    except Exception as e:
        logging.exception("Namuna preview yaratishda xatolik")
        await message.answer(f"⚠️ Xatolik yuz berdi: {e}")
        await state.clear()
        return

    pending_payments[uid] = {
        "file_path": file_path,
        "photo_path": photo_path,
        "preview_dir": preview_dir,
        "fish": data.get("fish") or "Noma'lum",
        "username": message.from_user.username or "",
        "telegram_name": message.from_user.full_name or "",
        "status": "waiting_receipt",
    }

    for preview_path in preview_paths:
        await message.answer_photo(
            FSInputFile(preview_path),
            caption="👀 <b>MA'LUMOTNOMA HUJJAT NAMUNASI</b>\nOriginal Word fayl to'lov tasdiqlangandan keyin yuboriladi.",
            parse_mode="HTML"
        )

    await message.answer(
        "💳 <b>TO'LOV QILISH</b>\n\n"
        f"📄 Narxi: <b>{PAYMENT_AMOUNT}</b>\n"
        f"💳 Karta: <code>{PAYMENT_CARD}</code>\n"
        f"👤 Egasi: <b>{CARD_OWNER}</b>\n\n"
        "To'lov qilib, chekni shu yerga yuboring:",
        parse_mode="HTML"
    )
    await state.set_state(Form.payment_receipt)

@dp.message(Form.payment_receipt, F.photo | F.document)
async def process_payment_receipt(message: Message, state: FSMContext):
    uid = message.from_user.id
    info = pending_payments.get(uid)
    if not info:
        await message.answer("❌ Ma'lumot topilmadi. /start ni bosing.")
        return

    receipt_path = f"downloads/receipt_{uid}.jpg"
    if message.photo:
        file_info = await bot.get_file(message.photo[-1].file_id)
        await bot.download_file(file_info.file_path, destination=receipt_path)
    else:
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, destination=receipt_path)

    info["receipt_path"] = receipt_path
    info["status"] = "waiting_admin"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ TASDIQLASH", callback_data=f"payment_approve:{uid}"),
        InlineKeyboardButton(text="❌ RAD ETISH", callback_data=f"payment_reject:{uid}"),
    ]])

    await bot.send_photo(
        ADMIN_ID,
        FSInputFile(receipt_path),
        caption=f"💰 <b>YANGI CHEK</b>\n👤 FIO: <b>{info['fish']}</b>\n🆔 ID: <code>{uid}</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    await message.answer("✅ Chekingiz adminga yuborildi. 15 daqiqada tekshiriladi.")
    await state.clear()

@dp.callback_query(F.data.startswith("payment_approve:"))
async def payment_approve(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    uid = int(callback.data.split(":", 1)[1])
    info = pending_payments.get(uid)
    if not info: return

    await bot.send_document(
        uid, FSInputFile(info["file_path"]),
        caption="✅ <b>To'lovingiz tasdiqlandi! Mana hujjatning originali:</b>", parse_mode="HTML", reply_markup=start_keyboard()
    )
    await callback.message.edit_caption(caption="✅ TO'LOV TASDIQLANDI")
    pending_payments.pop(uid, None)
    await callback.answer("Bajarildi!")

@dp.callback_query(F.data.startswith("payment_reject:"))
async def payment_reject(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    uid = int(callback.data.split(":", 1)[1])
    info = pending_payments.get(uid)
    if not info: return

    await bot.send_message(uid, "❌ To'lov chekingiz tasdiqlanmadi. Qaytadan yuboring.")
    await callback.message.edit_caption(caption="❌ RAD ETILDI")
    info["status"] = "waiting_receipt"
    await callback.answer("Rad etildi.")

@dp.message(Command("myid"))
async def myid_command(message: Message):
    await message.answer(f"Sizning ID: <code>{message.from_user.id}</code>", parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
