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

# Shablon faylning mutlaq manzilini aniqlaymiz
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

# Doimiy START tugmasi
def start_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="START")]],
        resize_keyboard=True,
        is_persistent=True
    )

# Har bir savolda ko'rsatiladigan YO'Q tugmasi
def no_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="YO'Q")]
        ],
        resize_keyboard=True
    )

def answer_value(message: Message):
    """YO'Q tugmasi bosilsa hujjatga aynan 'Yo'q' yoziladi."""
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
    await message.answer(
        "Tug'ilgan yilingizni kiriting (masalan: 13.05.2000-yil):",
        reply_markup=no_keyboard()
    )
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
    await message.answer("Xalq deputatlari respublika, viloyat, shahar va tuman Kengashi deputatimisiz yoki boshqa saylanadigan organ a'zosi? (To'liq yozing):", reply_markup=no_keyboard())
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

def create_preview_with_watermark(docx_path, uid):
    try:
        import win32com.client
    except ImportError:
        raise RuntimeError("pywin32 o'rnatilmagan.")

    import fitz
    from PIL import Image, ImageDraw, ImageFont

    preview_dir = os.path.join("downloads", f"preview_{uid}")
    os.makedirs(preview_dir, exist_ok=True)
    pdf_path = os.path.join(preview_dir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")

    word = None
    document = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(os.path.abspath(docx_path), ReadOnly=True, AddToRecentFiles=False)
        document.ExportAsFixedFormat(
            OutputFileName=os.path.abspath(pdf_path),
            ExportFormat=17, OpenAfterExport=False, OptimizeFor=0, Range=0, Item=0
        )
    except Exception as e:
        raise RuntimeError(f"Microsoft Word orqali preview yaratilmadi. Xato: {e}")
    finally:
        try:
            if document: document.Close(False)
        except: pass
        try:
            if word: word.Quit()
        except: pass

    if not os.path.exists(pdf_path):
        raise RuntimeError("Word PDF faylini yaratmadi.")

    pdf = fitz.open(pdf_path)
    preview_paths = []
    try:
        font_candidates = [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\calibrib.ttf"]
        font_path = next((p for p in font_candidates if os.path.exists(p)), None)

        for page_index, page in enumerate(pdf):
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            png_path = os.path.join(preview_dir, f"namuna_{page_index + 1}.png")
            pix.save(png_path)

            image = Image.open(png_path).convert("RGBA")
            overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            font_size = max(60, min(image.size) // 5)
            font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()

            bbox = draw.textbbox((0, 0), "NAMUNA", font=font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

            watermark = Image.new("RGBA", (text_w + 120, text_h + 120), (255, 255, 255, 0))
            wd = ImageDraw.Draw(watermark)
            wd.text((60, 60), "NAMUNA", font=font, fill=(80, 80, 80, 75), stroke_width=2, stroke_fill=(255, 255, 255, 40))
            watermark = watermark.rotate(35, expand=True, resample=Image.Resampling.BICUBIC)

            x = (image.width - watermark.width) // 2
            y = (image.height - watermark.height) // 2
            overlay.alpha_composite(watermark, (x, y))
            final_image = Image.alpha_composite(image, overlay).convert("RGB")
            final_image.save(png_path, format="PNG", optimize=True)
            preview_paths.append(png_path)
    finally:
        pdf.close()

    return preview_paths, preview_dir

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

    # Mutlaq manzil orqali shablon ochiladi
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
        preview_paths, preview_dir = create_preview_with_watermark(file_path, uid)
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
            caption="👀 <b>MA'LUMOTNOMA NAMUNASI</b>\nOriginal fayl to'lov tasdiqlangandan keyin yuboriladi.",
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
        caption="✅ <b>To'lovingiz tasdiqlandi!</b>", parse_mode="HTML", reply_markup=start_keyboard()
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
