import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.enums import ChatMemberStatus

BOT_TOKEN = "8371434041:AAGnvrCL4Bb0JfcBxE0Fb4cnYD4Y3qAT0Jc"
CHANNEL_LINK = "https://t.me/+00hGhOja5G05MjBk"

# ❗ ВАЖНО: поставь РЕАЛЬНЫЙ id канала
CHANNEL_ID = -1002415070098

ADMIN_USERNAME = "cunpar"

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

user_chats = set()

# ---------- Проверка подписки ----------
async def check_sub(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь подписчиком канала CHANNEL_ID.
    Возвращает True, если подписан, иначе False.
    Работает корректно только если бот админ канала.
    """
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Подписан, если статус не left/kicked
        if member.status in ["creator", "administrator", "member", "restricted"]:
            return True
        else:
            return False
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False

# ---------- /start ----------
@dp.message(Command("start"))
async def start(msg: types.Message):
    # Сначала проверяем подписку
    is_subscribed = await check_sub(msg.from_user.id)

    if not is_subscribed:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check")]
        ])
        await msg.answer_photo(
            photo=FSInputFile("start.jpg"),
            caption="❗ Подпишись на канал для доступа",
            reply_markup=kb
        )
        return  # не добавляем в user_chats и не показываем панель

    # Если подписан, добавляем чат и показываем панель
    user_chats.add(msg.chat.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚨 ОТПРАВКА ЖАЛОБ", callback_data="ddos")],
        [InlineKeyboardButton(text="👤 О разработчике", callback_data="dev")],
        [InlineKeyboardButton(text="💎 Купить админку", callback_data="buy")]
    ])
    await msg.answer_photo(
        photo=FSInputFile("start.jpg"),
        caption="Добро пожаловать.",
        reply_markup=kb
    )

# ---------- Проверить подписку ----------
@dp.callback_query(F.data == "check")
async def recheck(call: types.CallbackQuery):
    await call.answer("🔍 Проверяем подписку...")
    is_subscribed = await check_sub(call.from_user.id)

    if not is_subscribed:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check")]
        ])
        await call.message.answer(
            "❗ Вы еще не подписаны на канал.",
            reply_markup=kb
        )
        return

    # Пользователь подписан — просто отправляем новое сообщение с панелью
    user_chats.add(call.message.chat.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚨 ОТПРАВКА ЖАЛОБ", callback_data="ddos")],
        [InlineKeyboardButton(text="👤 О разработчике", callback_data="dev")],
        [InlineKeyboardButton(text="💎 Купить админку", callback_data="buy")]
    ])
    await call.message.answer("Добро пожаловать.", reply_markup=kb)


# ---------- Снос с выбором юзернейма и жалобы ----------
user_ddos_data = {}  # временно хранит данные по каждому пользователю

@dp.callback_query(F.data == "ddos")
async def fake_ddos(call: types.CallbackQuery):
    await call.answer()
    await call.message.answer("🛠 Введите юзернейм, на который хотите отправить репорт (например, @target):")
    
    user_ddos_data[call.from_user.id] = {"step": "get_username", "chat_id": call.message.chat.id}


@dp.message()
async def handle_ddos_steps(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in user_ddos_data:
        return  # пользователь не в процессе “сноса”

    data = user_ddos_data[user_id]

    # Шаг 1: получаем юзернейм
    if data["step"] == "get_username":
        data["username"] = msg.text
        data["step"] = "get_reason"
        await msg.answer("📝 Введите причину/жалобу на пользователя:")
        return

    # Шаг 2: получаем жалобу
    if data["step"] == "get_reason":
        data["reason"] = msg.text
        data["step"] = "simulate"
        await msg.answer("▶ Инициализация репорта...")

        msg_sim = await msg.answer("▶ Подключение к узлам...")

        steps = [
            f"▶ Отправка жалобы от @{msg.from_user.username} к {data['username']} [▓▓░░░░░░░░] 20%",
            f"▶ Отправка жалобы [▓▓▓▓▓░░░░░] 50%",
            f"▶ Отправка жалобы [▓▓▓▓▓▓▓▓░░] 80%",
            f"▶ УСПЕШНО ✅ Репорт отправлен от @{msg.from_user.username} к {data['username']}\nПричина: {data['reason']}"
        ]

        for s in steps:
            await asyncio.sleep(1.3)
            await msg_sim.edit_text(s)

        # очистка данных после завершения
        user_ddos_data.pop(user_id)
# ---------- Кнопки ----------
@dp.callback_query(F.data == "dev")
async def dev(call):
    await call.answer()
    await call.message.answer("👤 Разработчик: @uselli")

@dp.callback_query(F.data == "buy")
async def buy(call):
    await call.answer()
    await call.message.answer("💎 Купить админку: @cunpar")

# ---------- /post ----------
@dp.message(Command("post"))
async def post(msg: types.Message):
    if msg.from_user.username != ADMIN_USERNAME:
        return

    text = msg.text.replace("/post", "").strip()
    if not text:
        return

    for chat in user_chats:
        try:
            await bot.send_message(chat, text)
        except:
            pass

# ---------- Запуск ----------
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
