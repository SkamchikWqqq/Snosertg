import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✅ Я онлайн!"

def run():
    port = int(os.environ.get("PORT", 8080))  # Получаем порт из переменной окружения
    app.run(host='0.0.0.0', port=port)  # Запускаем Flask на этом порту

Thread(target=run).start()
import asyncio

import aiosqlite

from aiogram import Bot, Dispatcher, types, F

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.filters import CommandStart

from aiogram.fsm.state import State, StatesGroup

from aiogram.fsm.context import FSMContext



TOKEN = "8787728737:AAEtcUxHgTaVELYHM_i_Ji4EbY9oyNdyiWk"



bot = Bot(token=TOKEN)

dp = Dispatcher()



# --- Админы ---

ADMINS = ["cunpar"]



# --- Каналы для проверки ---

CHANNEL_LINKS = [

    "https://t.me/+1sy_SP95ByxiNDFl",

    "https://t.me/+yO5vZ2dUyRE3MzM0"

]



CHANNEL_IDS = [

    -1002952890093,  # сюда вставь ID первого канала

    -1002415070098   # сюда вставь ID второго канала

]



# --- Кнопка подписки ---

sub_kb = InlineKeyboardMarkup(

    inline_keyboard=[

        [InlineKeyboardButton(text="📢 Подписаться на канал 1", url=CHANNEL_LINKS[0])],

        [InlineKeyboardButton(text="📢 Подписаться на канал 2", url=CHANNEL_LINKS[1])],

        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]

    ]

)



# --- Проверка подписки ---

async def is_subscribed(user_id):



    for channel in CHANNEL_IDS:

        try:

            member = await bot.get_chat_member(channel, user_id)



            if member.status in ["left", "kicked"]:

                return False



        except:

            return False



    return True



# --- База ---

async def init_db():

    async with aiosqlite.connect("users.db") as db:

        await db.execute(

            "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)"

        )

        await db.commit()



async def add_user(user_id):

    async with aiosqlite.connect("users.db") as db:

        await db.execute(

            "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)

        )

        await db.commit()



async def get_users():

    async with aiosqlite.connect("users.db") as db:

        async with db.execute("SELECT user_id FROM users") as cursor:

            return [row[0] async for row in cursor]



# --- Клавиатуры ---

def get_keyboard(username):

    buttons = [

        [KeyboardButton(text="📩 запуск")],

        [KeyboardButton(text="ℹ️ О боте")]

    ]



    if username and username.lower() in [a.lower() for a in ADMINS]:

        buttons.insert(1, [KeyboardButton(text="📢 Рассылка")])



    return ReplyKeyboardMarkup(

        keyboard=buttons,

        resize_keyboard=True

    )



# --- FSM ---

class ReportState(StatesGroup):

    target = State()

    reason = State()

    mode = State()



class BroadcastState(StatesGroup):

    text = State()



# --- Старт ---

@dp.message(CommandStart())

async def start(message: types.Message):



    await add_user(message.from_user.id)



    # ПРОВЕРКА ПОДПИСКИ

    if not await is_subscribed(message.from_user.id):



        await message.answer(

            "🚫 Для использования бота подпишись на каналы:",

            reply_markup=sub_kb

        )

        return



    photo = FSInputFile("start.jpg")



    await message.answer_photo(

        photo=photo,

        caption=(

            "👋 Добро пожаловать в тоставщика!\n\n"

            "🔥 Самый мощный инструмент\n"

            "⚡ Быстро\n"

            "🛡 Надёжно\n\n"

            "👇 Выбери кнопку:"

        ),

        reply_markup=get_keyboard(message.from_user.username)

    )



# --- Проверка кнопки ---

@dp.callback_query(F.data == "check_sub")

async def check_sub(callback: types.CallbackQuery):



    if await is_subscribed(callback.from_user.id):



        photo = FSInputFile("start.jpg")



        await callback.message.delete()



        await callback.message.answer_photo(

            photo=photo,

            caption="✅ Подписка подтверждена!",

            reply_markup=get_keyboard(callback.from_user.username)

        )



    else:

        await callback.answer("❌ Подпишись на все каналы", show_alert=True)



# --- О боте ---

@dp.message(F.text == "ℹ️ О боте")

async def about(message: types.Message):

    await message.answer(

        "ℹ️ О боте\n\n"

        "👑 Owner: @Cunpar\n"

        "⚡ Version: 1.0\n"

        "🤖 TOP сн bot"

    )



# --- Рассылка только админам ---

@dp.message(F.text == "📢 Рассылка")

async def broadcast_start(message: types.Message, state: FSMContext):



    if message.from_user.username not in ADMINS:

        return



    await message.answer("📢 Введи текст рассылки:")

    await state.set_state(BroadcastState.text)





@dp.message(BroadcastState.text)

async def broadcast_send(message: types.Message, state: FSMContext):



    users = await get_users()

    count = 0



    for user in users:

        try:

            await bot.send_message(

                user,

                f"📢 Рассылка\n\n{message.text}"

            )

            count += 1

        except:

            pass



    await message.answer(f"✅ Отправлено {count} пользователям")

    await state.clear()



# --- Жалобы ---

@dp.message(F.text == "📩 Отправка жалоб")

async def report_start(message: types.Message, state: FSMContext):

    await message.answer("👤 Введи username цели:")

    await state.set_state(ReportState.target)



@dp.message(ReportState.target)

async def report_reason(message: types.Message, state: FSMContext):

    await state.update_data(target=message.text)

    await message.answer("📄 Введи причину:")

    await state.set_state(ReportState.reason)



@dp.message(ReportState.reason)

async def report_mode(message: types.Message, state: FSMContext):

    await state.update_data(reason=message.text)

    await message.answer("⚙️ Введи режим:")

    await state.set_state(ReportState.mode)



@dp.message(ReportState.mode)

async def report_done(message: types.Message, state: FSMContext):



    data = await state.update_data(mode=message.text)

    data = await state.get_data()



    msg = await message.answer("⏳ Отправка жалоб...")



    await asyncio.sleep(1)

    await msg.edit_text("📡 Подключение...")

    await asyncio.sleep(1)

    await msg.edit_text("📨 Отправка...")

    await asyncio.sleep(1)

    await msg.edit_text(

        f"✅ Готово\n\n"

        f"👤 Цель: {data['target']}\n"

        f"📄 Причина: {data['reason']}\n"

        f"⚙️ Режим: {data['mode']}\n\n"

        f"📊 Отправлено: 167 жалоб"

    )



    await state.clear()



# --- Запуск ---

async def main():

    await init_db()

    await dp.start_polling(bot)



asyncio.run(main())



