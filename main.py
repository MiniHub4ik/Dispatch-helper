import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import F
import os
from dotenv import load_dotenv

# ---------------- CONFIG ----------------
load_dotenv()  # загружает .env

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ---------------- TERMS (static) ----------------
terms_eng = {
    "📦 Basics": {
        "Load": "Cargo or shipment that is transported from one location to another. Example: a truckload of drinks from Coca-Cola’s warehouse to Walmart.",
        "Pickup (PU)": "The exact location and scheduled time where the driver collects the cargo. Example: driver must be at the warehouse by 10:00 AM.",
        "Delivery (DEL)": "The final location where the cargo must be unloaded and delivered. Example: store distribution center.",
        "Shipper": "The company or person who sends the cargo. Example: Pepsi, Amazon warehouse.",
        "Consignee / Receiver": "The company or person who receives the cargo. Example: Walmart, Costco.",
        "Driver": "The truck driver responsible for transporting the load safely and on time.",
    },
    "🕐 Time & Status": {
        "ETA": "Estimated Time of Arrival — when the driver is expected to arrive. Example: ETA 3:45 PM.",
        "ETD": "Estimated Time of Departure — when the driver is expected to leave. Example: ETD 7:00 AM from warehouse.",
        "On Time": "Cargo is expected to be delivered according to the schedule.",
        "Delay": "The driver or cargo is late for pickup/delivery. Can be due to traffic, weather, or warehouse delays.",
        "Check call": "A regular call from the driver to update location and status. Example: 'I’m 100 miles away, arriving in 2 hours.'",
        "In transit": "The cargo is currently on the road, moving towards its destination.",
        "Empty / Available": "The driver has no load and is ready for the next shipment.",
        "Loaded / Under load": "The driver currently has a cargo on board and is delivering it.",
    },
    "📑 Documents": {
        "BOL": "Bill of Lading — the main legal shipping document. Includes shipper, receiver, cargo details, and must be signed.",
        "POD": "Proof of Delivery — signed paper confirming that cargo was delivered successfully.",
        "Rate confirmation": "Agreement between broker and carrier confirming the freight rate, route, and terms of shipment.",
        "Lumper receipt": "Receipt for unloading services (paid when warehouse staff unloads the truck).",
    },
    "💸 Money & Rates": {
        "Rate": "The total payment agreed for transporting the load.",
        "TONU": "Truck Ordered, Not Used — money paid if a truck was ordered but the load got cancelled.",
        "Detention": "Extra payment when a driver waits longer than free time (usually after 2 free hours).",
        "Layover": "Payment for when the driver must wait overnight due to delay or schedule change.",
    },
    "🚚 Equipment & Locations": {
        "Facility / Warehouse": "A place where goods are stored, loaded, or unloaded.",
        "Dock": "The ramp/platform where trucks are loaded and unloaded.",
        "Drop & Hook": "Driver drops off an empty trailer and picks up a loaded one — no waiting.",
        "Live load / unload": "Driver waits while cargo is being loaded/unloaded (can take hours).",
        "Trailer": "The big container part of the truck where cargo is carried.",
        "Dry van": "Standard closed trailer for regular goods (boxes, pallets, furniture).",
        "Reefer": "Refrigerated trailer with cooling for perishable goods (meat, milk, fruits).",
        "Flatbed": "Open trailer for oversized or heavy loads (steel, machinery, lumber).",
        "Pallet Jack": "A manual tool to move pallets inside the warehouse.",
        "Forklift": "A powered machine with forks to lift and move pallets or heavy goods.",
    },
    "📞 Communication": {
        "Dispatcher": "The person who gives loads to drivers, tracks them, and solves problems.",
        "Broker": "Middleman who finds loads from shippers and gives them to carriers for a fee.",
        "Update": "Information about the current status of the load (location, ETA, issues).",
        "Check in / Check out": "Driver reports arrival or departure from a warehouse/facility.",
    }
}

terms_rus = {
    "📦 Основные": {
        "Load": "Груз или партия товара, перевозимая из точки А в точку Б. Пример: фура с напитками от Coca-Cola на склад Walmart.",
        "Pickup (PU)": "Место и время, где водитель должен забрать груз. Пример: склад Amazon, время — 10:00.",
        "Delivery (DEL)": "Место выгрузки и передачи груза. Пример: распределительный центр магазина.",
        "Shipper": "Компания или лицо, которое отправляет груз. Пример: Pepsi, Amazon.",
        "Consignee / Receiver": "Компания или лицо, получающее груз. Пример: Walmart, Costco.",
        "Driver": "Водитель грузовика, который перевозит груз безопасно и вовремя.",
    },
    "🕐 Время и статусы": {
        "ETA": "Ожидаемое время прибытия. Пример: ETA 15:45.",
        "ETD": "Ожидаемое время выезда. Пример: ETD 07:00 со склада.",
        "On Time": "Груз доставлен по расписанию.",
        "Delay": "Опоздание груза или водителя. Причины: пробки, погода, задержка на складе.",
        "Check call": "Звонок от водителя с обновлением статуса. Пример: «Осталось 100 миль, буду через 2 часа».",
        "In transit": "Груз находится в пути.",
        "Empty / Available": "Водитель свободен, готов к следующему грузу.",
        "Loaded / Under load": "Водитель уже загружен и выполняет доставку.",
    },
    "📑 Документы": {
        "BOL": "Bill of Lading (транспортная накладная) — главный документ перевозки. В нём указаны отправитель, получатель, груз и подписи сторон.",
        "POD": "Proof of Delivery (подтверждение доставки) — документ с подписью о том, что груз получен.",
        "Rate confirmation": "Документ, где зафиксирована ставка, маршрут и условия перевозки между брокером и перевозчиком.",
        "Lumper receipt": "Квитанция за разгрузку (когда разгрузкой занимаются сотрудники склада).",
    },
    "💸 Деньги и ставки": {
        "Rate": "Общая сумма оплаты за перевозку груза.",
        "TONU": "Truck Ordered, Not Used — компенсация, если машину заказали, а груз отменили.",
        "Detention": "Оплата за простой, если водитель ждёт дольше бесплатного времени (обычно после 2-х часов).",
        "Layover": "Оплата за ночёвку водителя при задержке или переносе рейса.",
    },
    "🚚 Места и оборудование": {
        "Facility / Warehouse": "Склад, где хранят, грузят или разгружают товары.",
        "Dock": "Погрузочная рампа/площадка для машин.",
        "Drop & Hook": "Оставить пустой трейлер и забрать загруженный (без ожидания).",
        "Live load / unload": "Загрузка/разгрузка прицепа при водителе (может занять много времени).",
        "Trailer": "Прицеп грузовика, где находится груз.",
        "Dry van": "Закрытый стандартный трейлер для обычных товаров (коробки, мебель).",
        "Reefer": "Холодильный трейлер для скоропортящихся товаров (молоко, мясо, овощи).",
        "Flatbed": "Открытая платформа для тяжёлых или негабаритных грузов (металл, техника, лес).",
        "Pallet Jack": "Рохля — ручная тележка для перемещения паллет внутри склада.",
        "Forklift": "Погрузчик — техника для подъёма и перемещения тяжёлых грузов и паллет.",
    },
    "📞 Коммуникация": {
        "Dispatcher": "Диспетчер — человек, который распределяет грузы, следит за водителями и решает проблемы.",
        "Broker": "Брокер — посредник между отправителем и перевозчиком, зарабатывает комиссию.",
        "Update": "Информация о текущем статусе груза (где он, когда прибудет, есть ли проблемы).",
        "Check in / Check out": "Отметка водителя о прибытии или выезде со склада.",
    }
}

terms_uz = {
    "📦 Asosiy": {
        "Load": "Yuk yoki tashiladigan tovar. Bir joydan ikkinchi joyga olib boriladi.",
        "Pickup (PU)": "Haydovchi yukni oladigan aniq joy va vaqt.",
        "Delivery (DEL)": "Yukni tushirish va yetkazib berish manzili.",
        "Shipper": "Yukni yuboradigan kompaniya yoki shaxs.",
        "Consignee / Receiver": "Yukni qabul qiladigan kompaniya yoki shaxs.",
        "Driver": "Yuk mashinasi haydovchisi, yukni tashiydi.",
    },
    "🕐 Vaqt va statuslar": {
        "ETA": "Kutilayotgan kelish vaqti.",
        "ETD": "Kutilayotgan jo‘nab ketish vaqti.",
        "On Time": "Yuk o‘z vaqtida yetib keladi.",
        "Delay": "Yuk yoki haydovchi kechikmoqda.",
        "Check call": "Haydovchidan joylashuvini so‘rash uchun qo‘ng‘iroq.",
        "In transit": "Yuk yo‘lda, manzilga yetkazilmoqda.",
        "Empty / Available": "Haydovchi bo‘sh va yangi yukka tayyor.",
        "Loaded / Under load": "Haydovchida yuk bor, tashib ketmoqda.",
    },
    "📑 Hujjatlar": {
        "BOL": "Bill of Lading — yuk hujjati, yuk tafsilotlarini tasdiqlaydi.",
        "POD": "Proof of Delivery — yuk yetkazilganini tasdiqlovchi imzo.",
        "Rate confirmation": "Yuk stavkasi bo‘yicha kelishuv.",
        "Lumper receipt": "Yuk tushirish/xizmat uchun kvitansiya.",
    },
    "💸 Pul va stavkalar": {
        "Rate": "Yukni tashish uchun belgilangan to‘lov.",
        "TONU": "Mashina chaqirilib, yuk berilmasa to‘lanadigan kompensatsiya.",
        "Detention": "Haydovchi ko‘p kutganida qo‘shimcha to‘lov (odatda 2 soatdan keyin).",
        "Layover": "Haydovchi tunab qolsa yoki uzoq kutishga majbur bo‘lsa, qo‘shimcha to‘lov.",
    },
    "🚚 Jihoz va joylar": {
        "Facility / Warehouse": "Ombor, yuk saqlanadigan yoki ortiladigan joy.",
        "Dock": "Mashinalar yuklanadigan yoki tushiriladigan platforma.",
        "Drop & Hook": "Bo‘sh treyler qoldiriladi, yuklangan treyler olinadi.",
        "Live load / unload": "Haydovchi yuk ortilishini yoki tushirilishini kutadi.",
        "Trailer": "Yuk tashiladigan mashinaning orqa qismi.",
        "Dry van": "Oddiy yopiq treyler.",
        "Reefer": "Muzlatkichli treyler, tez buziladigan mahsulotlar uchun.",
        "Flatbed": "Ochiq treyler, katta yuklar uchun.",
        "Pallet Jack": "Ruchnoy roxlya — palletalarni qo‘lda ko‘chirish uchun.",
        "Forklift": "Pogruzchik — palletalarni ko‘tarish va tashish uchun texnika.",
    },
    "📞 Aloqa": {
        "Dispatcher": "Reyslarni muvofiqlashtiradigan odam.",
        "Broker": "Yuk beruvchi va tashuvchi o‘rtasida vositachi.",
        "Update": "Yukning hozirgi statusi haqida ma’lumot.",
        "Check in / Check out": "Haydovchining omborga kelish yoki chiqishini belgilash.",
    }
}

terms_dicts = {"eng": terms_eng, "rus": terms_rus, "uz": terms_uz}
user_lang = {}  # хранит язык для каждого пользователя

# ---------------- DATABASE ----------------
conn = sqlite3.connect("templates.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    text TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY
)
""")
conn.commit()

last_message = {}

# ---------------- FSM ----------------
class AddTemplate(StatesGroup):
    waiting_for_text = State()

class EditTemplate(StatesGroup):
    waiting_for_text = State()

class Broadcast(StatesGroup):
    waiting_for_photo = State()
    waiting_for_text = State()
    confirm = State()

# ---------------- MAIN MENU ----------------
@dp.message(Command("start"))
async def start(message: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (message.from_user.id,))
    conn.commit()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Terms/Термины/Terminlar", callback_data="menu:terms")],
            [InlineKeyboardButton(text="📝 Templates", callback_data="menu:templates")],
            [InlineKeyboardButton(text="⚙️ Admin", callback_data="menu:admin")]
        ]
    )
    msg = await message.answer("Choose section:", reply_markup=kb)
    last_message[message.chat.id] = msg.message_id

# ---------------- TERMS ----------------
@dp.callback_query(lambda c: c.data == "menu:terms")
async def show_terms(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇬🇧 Eng", callback_data="terms:eng")],
            [InlineKeyboardButton(text="🇷🇺 Rus", callback_data="terms:rus")],
            [InlineKeyboardButton(text="🇺🇿 Uzb", callback_data="terms:uz")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
        ]
    )

    await clean_and_send(callback, "📚 Choose language:", kb)


@dp.callback_query(lambda c: c.data.startswith("terms:"))
async def show_terms_categories(callback: types.CallbackQuery):
    lang = callback.data.split(":")[1]
    user_lang[callback.from_user.id] = lang
    terms = terms_dicts[lang]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}")]
                         for cat in terms.keys()] +
                        [[InlineKeyboardButton(text="⬅️ Back", callback_data="menu:terms")]]
    )
    await clean_and_send(callback, "📚 Categories:", kb)


@dp.callback_query(lambda c: c.data.startswith("cat:"))
async def show_category(callback: types.CallbackQuery):
    cat = callback.data.split(":", 1)[1]
    lang = user_lang.get(callback.from_user.id, "eng")
    terms = terms_dicts[lang]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=term, callback_data=f"term:{cat}:{term}")]
                         for term in terms[cat].keys()] +
                        [[InlineKeyboardButton(text="⬅️ Back", callback_data="terms:" + lang)]]
    )
    await clean_and_send(callback, f"<b>{cat}</b>\nChoose a term:", kb)


@dp.callback_query(lambda c: c.data.startswith("term:"))
async def show_term(callback: types.CallbackQuery):
    _, cat, term = callback.data.split(":", 2)
    lang = user_lang.get(callback.from_user.id, "eng")
    terms = terms_dicts[lang]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Back", callback_data=f"cat:{cat}")]]
    )
    await clean_and_send(callback, f"<b>{term}</b>\n{terms[cat][term]}", kb)


# ---------------- USER TEMPLATES ----------------
@dp.callback_query(lambda c: c.data == "menu:templates")
async def list_templates(callback: types.CallbackQuery):
    cursor.execute("SELECT id, title FROM templates")
    rows = cursor.fetchall()
    if rows:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=title, callback_data=f"tpl:{tpl_id}")]
                             for tpl_id, title in rows] +
                            [[InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]]
        )
        await clean_and_send(callback, "📝 Templates list:", kb)
    else:
        await clean_and_send(callback, "No templates yet. Add some in Admin.",
                             InlineKeyboardMarkup(
                                 inline_keyboard=[[InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]]))


@dp.callback_query(lambda c: c.data.startswith("tpl:"))
async def show_template(callback: types.CallbackQuery):
    tpl_id = int(callback.data.split(":")[1])
    cursor.execute("SELECT title, text FROM templates WHERE id = ?", (tpl_id,))
    row = cursor.fetchone()
    if row:
        title, text = row
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Back", callback_data="menu:templates")]]
        )
        await clean_and_send(callback, f"<b>{title}</b>\n<pre>{text}</pre>", kb)



# ---------------- ADMIN MENU ----------------
@dp.callback_query(lambda c: c.data == "menu:admin")
async def admin_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("⛔ Access denied", show_alert=True)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Add template", callback_data="admin:add_template")],
            [InlineKeyboardButton(text="📂 Manage templates", callback_data="admin:templates_list")],
            [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_main")]
        ]
    )
    await clean_and_send(callback, "⚙️ Admin panel:", kb)

# --- Broadcast flow ---
@dp.callback_query(lambda c: c.data == "admin:broadcast")
async def broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("⛔ Access denied", show_alert=True)

    await state.set_state(Broadcast.waiting_for_photo)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⏭ Skip", callback_data="broadcast:skip_photo")]]
    )
    await callback.message.answer("📸 Send me a photo or press Skip.", reply_markup=kb)

@dp.message(Broadcast.waiting_for_photo, F.photo)
async def broadcast_get_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await state.set_state(Broadcast.waiting_for_text)
    await message.answer("📝 Now send me the text of your article.")

@dp.callback_query(lambda c: c.data == "broadcast:skip_photo")
async def broadcast_skip_photo(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(photo=None)
    await state.set_state(Broadcast.waiting_for_text)
    await callback.message.answer("📝 Now send me the text of your article.")

@dp.message(Broadcast.waiting_for_text)
async def broadcast_get_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    data = await state.get_data()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Send to Everyone", callback_data="broadcast:send")],
            [InlineKeyboardButton(text="⬅️ Cancel", callback_data="menu:admin")]
        ]
    )
    if data.get("photo"):
        await message.answer_photo(data["photo"], caption=data["text"], reply_markup=kb)
    else:
        await message.answer(data["text"], reply_markup=kb)
    await state.set_state(Broadcast.confirm)

@dp.callback_query(lambda c: c.data == "broadcast:send")
async def broadcast_send(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("⛔ Access denied", show_alert=True)

    data = await state.get_data()
    text = data.get("text", "")
    photo = data.get("photo")

    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    count = 0
    for (user_id,) in users:
        try:
            if photo:
                await bot.send_photo(user_id, photo, caption=text)
            else:
                await bot.send_message(user_id, text)
            count += 1
        except:
            pass

    await state.clear()
    await callback.message.answer(f"✅ Broadcast sent to {count} users.")

# ---------------- BACK MAIN ----------------
@dp.callback_query(lambda c: c.data == "back_main")
async def back_main(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Terms/Термины", callback_data="menu:terms")],
            [InlineKeyboardButton(text="📝 Templates", callback_data="menu:templates")],
            [InlineKeyboardButton(text="⚙️ Admin", callback_data="menu:admin")]
        ]
    )
    await clean_and_send(callback, "Choose section:", kb)

# ---------------- CLEAN HELPER ----------------
async def clean_and_send(callback, text, kb):
    chat_id = callback.message.chat.id
    try:
        await bot.delete_message(chat_id, last_message[chat_id])
    except:
        pass
    msg = await callback.message.answer(text, reply_markup=kb)
    last_message[chat_id] = msg.message_id

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
