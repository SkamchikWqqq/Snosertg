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

# Обновленные ссылки на каналы
CHANNEL_1_LINK = "https://t.me/+00hGhOja5G05MjBk" 
CHANNEL_1_ID = -1002415070098 

CHANNEL_2_LINK = "https://t.me/+UV1hz_mo2iJjZDFi" 
CHANNEL_2_ID = -1002904646756 

CHANNEL_3_LINK = "https://t.me/+NEW_CHANNEL_LINK"  # Замените на ссылку вашего третьего канала
CHANNEL_3_ID = -100NEW_CHANNEL_ID  # Замените на ID вашего третьего канала

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
        member1 = await bot.get_chat_member(CHANNEL_1_ID, user_id) 
        member2 = await bot.get_chat_member(CHANNEL_2_ID, user_id) 
        member3 = await bot.get_chat_member(CHANNEL_3_ID, user_id) 

        if member1.status in ["creator", "administrator", "member", "restricted"] and 
           member2.status in ["creator", "administrator", "member", "restricted"] and 
           member3.status in ["creator", "administrator", "member", "restricted"]:
            return True 
        
        return False 
    except: 
        # Если бот не админ — считаем подписку ОК
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
            [InlineKeyboardButton(text="📢 Канал 1", url=CHANNEL_1_LINK)], 
            [InlineKeyboardButton(text="📢 Канал 2", url=CHANNEL_2_LINK)], 
            [InlineKeyboardButton(text="📢 Канал 3", url=CHANNEL_3_LINK)],  # Новый канал
            [InlineKeyboardButton(text="✅ Проверить", callback_data="check")] 
        ]) 
        await msg.answer_photo( 
            FSInputFile("start.jpg"), 
            caption="❗ Подпишись на каналы", 
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
        "✅ Доступ открыт"
    )

# Запуск бота
if __name__ == "__main__":
    from aiogram import executor
    
    # Запускаем поллинг
    executor.start_polling(dp, skip_updates=True)
