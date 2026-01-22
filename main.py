import asyncio
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from aiohttp import web  # ← ДОБАВЛЕНО


BOT_TOKEN = "8371434041:AAGnvrCL4Bb0JfcBxE0Fb4cnYD4Y3qAT0Jc"


# Канал 1
CHANNEL_LINK = "https://t.me/+00hGhOja5G05MjBk"
CHANNEL_ID = -1002415070098

# Канал 2
CHANNEL_2_LINK = "https://t.me/+UV1hz_mo2iJjZDFi"
CHANNEL_2_ID = -1002904646756

ADMIN_USERNAME = "cunpar"


bot = Bot(BOT_TOKEN)
dp = Dispatcher()

user_chats = set()
post_wait = set()


# ---------- ВЕБ-СЕРВЕР ДЛЯ RENDER (ДОБАВЛЕНО) ----------
async def web_handler(request):
    return web.Response(text="OK")

async def start_web():
    app = web.Application()
    app.router.add_get("/", web_handler)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
# ----------------------------------------------------


# ---------- Проверка подписки ----------
async def check_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["creator", "administrator", "member", "restricted"]:
            return True
        return False
    except:
        return False


# ---------- Панель ----------
def panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚨 ОТПРАВКА ЖАЛОБ", callback_data="ddos")],
        [InlineKeyboardButton(text="📨 POST", callback_data="post_btn")],
        [InlineKeyboardButton(text="👤 О разработчике", callback_data="dev")],
        [InlineKeyboardButton(text="💎 Купить админку", callback_data="buy")]
    ])


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
            caption="❗ Подпишись на ОБА канала",
            reply_markup=kb
        )
        return

    user_chats.add(msg.chat.id)
    await msg.answer_photo(
        FSInputFile("start.jpg"),
        caption="Добро пожаловать.",
        reply_markup=panel_kb()
    )


# ---------- Проверка ----------
@dp.callback_query(F.data == "check")
async def recheck(call: types.CallbackQuery):
    await call.answer("🔍 Проверяем...")
    if not await check_sub(call.from_user.id):
        await call.message.answer("❗ Подписка не найдена.")
        return

    user_chats.add(call.message.chat.id)
    await call.message.answer("Добро пожаловать.", reply_markup=panel_kb())


# ---------- POST ----------
@dp.callback_query(F.data == "post_btn")
async def post_btn(call: types.CallbackQuery):
    if call.from_user.username != ADMIN_USERNAME:
        await call.answer("❌ Нет доступа", show_alert=True)
        return

    post_wait.add(call.from_user.id)
    await call.message.answer("✏️ Введите текст для рассылки:")


@dp.message()
async def post_text(msg: types.Message):
    if msg.from_user.id in post_wait:
        post_wait.remove(msg.from_user.id)
        text = msg.text

        for chat in user_chats:
            try:
                await bot.send_message(chat, text)
            except:
                pass

        try:
            await bot.send_message(CHANNEL_2_ID, text)
        except:
            pass

        await msg.answer("✅ Рассылка завершена")
        return


# ---------- Снос ----------
user_ddos_data = {}

@dp.callback_query(F.data == "ddos")
async def ddos(call):
    await call.answer()
    user_ddos_data[call.from_user.id] = {"step": "user"}
    await call.message.answer("🛠 Введите @username:")


@dp.message()
async def ddos_steps(msg: types.Message):
    uid = msg.from_user.id
    if uid not in user_ddos_data:
        return

    data = user_ddos_data[uid]
    if data["step"] == "user":
        data["user"] = msg.text
        data["step"] = "reason"
        await msg.answer("📝 Введите причину:")
        return

    msg_sim = await msg.answer("▶ Отправка...")
    for s in ["20%", "50%", "80%", "✅ Готово"]:
        await asyncio.sleep(1)
        await msg_sim.edit_text(s)

    user_ddos_data.pop(uid)


# ---------- Кнопки ----------
@dp.callback_query(F.data == "dev")
async def dev(call):
    await call.answer()
    await call.message.answer("👤 Разработчик: @usellio")


@dp.callback_query(F.data == "buy")
async def buy(call):
    await call.answer()
    await call.message.answer("💎 Купить админку: @cunpar")


# ---------- Запуск ----------
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.gather(
        dp.start_polling(bot),
        start_web()  # ← ВАЖНО
    )

if __name__ == "__main__":
    asyncio.run(main())
    

