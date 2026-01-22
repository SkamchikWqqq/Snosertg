import asyncio
import random
import string
import sqlite3

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

BOT_TOKEN = "8261296041:AAGb_dIyd2tlvMTb8FgQEeWiVkmswealz-s"

CHANNEL_LINK = "https://t.me/+00hGhOja5G05MjBk"
CHANNEL_ID = -1002415070098

CHANNEL_2_LINK = "https://t.me/+UV1hz_mo2iJjZDFi"
CHANNEL_2_ID = -1002904646756

ADMIN_USERNAMES = ["cunpar"]

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

user_chats = set()
post_wait = set()
promo_wait = set()

# ---------- БАЗА ----------
db = sqlite3.connect("bot.db")
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS promos (
    code TEXT PRIMARY KEY,
    active INTEGER
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS activated_promos (
    user_id INTEGER PRIMARY KEY,
    code TEXT
)
""")

db.commit()

# ---------- Проверка подписки ----------
async def check_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["creator", "administrator", "member", "restricted"]:
            return True
        return False
    except:
        # если бот не админ — считаем подписку ОК
        return True

# ---------- Проверка промо ----------
def has_promo(user_id: int) -> bool:
    return sql.execute(
        "SELECT 1 FROM activated_promos WHERE user_id = ?",
        (user_id,)
    ).fetchone() is not None

# ---------- Панель ----------
def panel_kb(is_admin=False):
    kb = [
        [InlineKeyboardButton(text="🚨 ОТПРАВКА ЖАЛОБ", callback_data="ddos")],
        [InlineKeyboardButton(text="🎟 АКТИВИРОВАТЬ ПРОМО", callback_data="promo")]
    ]

    if is_admin:
        kb.append([InlineKeyboardButton(text="📨 POST", callback_data="post_btn")])
        kb.append([InlineKeyboardButton(text="🎟 СОЗДАТЬ ПРОМО", callback_data="promo_create")])
        kb.append([InlineKeyboardButton(text="📊 БАЗА ПОЛЬЗОВАТЕЛЕЙ", callback_data="users_db")])

    kb.append([InlineKeyboardButton(text="👤 О разработчике", callback_data="dev")])
    kb.append([InlineKeyboardButton(text="💎 Купить админку", callback_data="buy")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


# ---------- /start ----------
@dp.message(Command("start"))
async def start(msg: types.Message):
    if not await check_sub(msg.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Канал 1", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="📢 Канал 2", url=CHANNEL_2_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check")]
        ])
        await msg.answer_photo(
            FSInputFile("start.jpg"),
            caption="❗ Подпишись на канал",
            reply_markup=kb
        )
        return

    sql.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?)",
        (msg.from_user.id, msg.from_user.username)
    )
    db.commit()

    user_chats.add(msg.chat.id)

    await msg.answer_photo(
        FSInputFile("start.jpg"),
        caption="Добро пожаловать.",
        reply_markup=panel_kb(msg.from_user.username in ADMIN_USERNAMES)
    )

# ---------- Проверка ----------
@dp.callback_query(F.data == "check")
async def recheck(call: types.CallbackQuery):
    if not await check_sub(call.from_user.id):
        await call.message.answer("❌ Подписка не найдена")
        return

    await call.message.answer(
        "✅ Доступ открыт",
        reply_markup=panel_kb(call.from_user.username in ADMIN_USERNAMES)
    )

# ---------- СОЗДАТЬ ПРОМО ----------
@dp.callback_query(F.data == "promo_create")
async def promo_create(call: types.CallbackQuery):
    if call.from_user.username not in ADMIN_USERNAMES:
        return

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    sql.execute("INSERT INTO promos VALUES (?, 1)", (code,))
    db.commit()

    await call.message.answer(f"🎟 Промокод создан:\n`{code}`", parse_mode="Markdown")

# ---------- АКТИВАЦИЯ ПРОМО ----------
@dp.callback_query(F.data == "promo")
async def promo_btn(call: types.CallbackQuery):
    promo_wait.add(call.from_user.id)
    await call.message.answer("🎟 Введите промокод:")

# ---------- POST ----------
@dp.callback_query(F.data == "post_btn")
async def post_btn(call: types.CallbackQuery):
    if call.from_user.username not in ADMIN_USERNAMES:
        await call.answer("❌ Нет доступа", show_alert=True)
        return

    post_wait.add(call.from_user.id)
    await call.message.answer("✏️ Введите текст для рассылки:")

# ---------- БАЗА ----------
@dp.callback_query(F.data == "users_db")
async def users_db(call: types.CallbackQuery):
    if call.from_user.username not in ADMIN_USERNAMES:
        return

    users = sql.execute("SELECT user_id, username FROM users").fetchall()
    text = f"📊 Пользователей: {len(users)}\n\n"

    for u in users[:30]:
        text += f"• @{u[1]} | {u[0]}\n"

    await call.message.answer(text)

# ---------- ТЕКСТ ----------
@dp.message()
async def handle_text(msg: types.Message):
    if msg.from_user.id in post_wait:
        post_wait.remove(msg.from_user.id)
        for chat in user_chats:
            try:
                await bot.send_message(chat, msg.text)
            except:
                pass
        await msg.answer("✅ Рассылка завершена")
        return

    if msg.from_user.id in promo_wait:
        promo_wait.remove(msg.from_user.id)
        code = msg.text.strip().upper()

        promo = sql.execute(
            "SELECT code FROM promos WHERE code = ? AND active = 1",
            (code,)
        ).fetchone()

        if not promo:
            await msg.answer("❌ Неверный промокод")
            return

        sql.execute("INSERT OR REPLACE INTO activated_promos VALUES (?, ?)", (msg.from_user.id, code))
        sql.execute("UPDATE promos SET active = 0 WHERE code = ?", (code,))
        db.commit()

        await msg.answer("✅ Промокод активирован")

# ---------- FSM СНОС ----------
class DdosForm(StatesGroup):
    username = State()
    reason = State()
    comment = State()

@dp.callback_query(F.data == "ddos")
async def start_ddos(call: types.CallbackQuery, state: FSMContext):
    if not has_promo(call.from_user.id):
        await call.message.answer("🔒 Активируйте промокод для доступа")
        return

    await call.message.answer("🎯 Введите юзернейм цели:")
    await state.set_state(DdosForm.username)

@dp.message(DdosForm.username)
async def ddos_username(msg: types.Message, state: FSMContext):
    await state.update_data(username=msg.text)
    await msg.answer("📄 Причина жалобы:")
    await state.set_state(DdosForm.reason)

@dp.message(DdosForm.reason)
async def ddos_reason(msg: types.Message, state: FSMContext):
    await state.update_data(reason=msg.text)
    await msg.answer("💬 Комментарий:")
    await state.set_state(DdosForm.comment)

@dp.message(DdosForm.comment)
async def ddos_comment(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    sim = await msg.answer("⚙️ Обработка...")

    for t in ["Проверка...", "Отправка...", "Готово"]:
        await asyncio.sleep(1.2)
        await sim.edit_text(t)

    await sim.edit_text(
        f"✅ Жалоба отправлена\n\n"
        f"🎯 {data['username']}\n"
        f"📄 {data['reason']}\n"
        f"💬 {msg.text}"
    )
    await state.clear()

# ---------- ИНФО ----------
@dp.callback_query(F.data == "dev")
async def dev(call):
    await call.message.answer("👤 Разработчик: @usellio")

@dp.callback_query(F.data == "buy")
async def buy(call):
    await call.message.answer("💎 Купить админку: @cunpar")

# ---------- ЗАПУСК ----------
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
