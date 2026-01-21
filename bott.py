from aiogram import Bot, Dispatcher, executor, types
import sqlite3

# ===== НАСТРОЙКИ =====
API_TOKEN = "8131856431:AAGCUaRzUvhl_TX__EnXfBXrlpmQsMPcASM"
ADMINS = [5844623745]  # ← ВСТАВЬ СЮДА СВОЙ user_id

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ===== БАЗА ДАННЫХ =====
conn = sqlite3.connect("data.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    description TEXT,
    reaction TEXT
)
""")
conn.commit()

# ===== ОПИСАНИЯ (то, что будут лайкать) =====
descriptions = [
    "Человек1. Описание1",
    "Человек2. Описание2",
    "Человек3. Описание3"
]

# ===== КНОПКИ =====
def like_keyboard(index):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("👍 Лайк", callback_data=f"like_{index}"),
        types.InlineKeyboardButton("👎 Дизлайк", callback_data=f"dislike_{index}")
    )
    return keyboard

# ===== /start =====
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user = message.from_user
    await message.answer(f"Привет, {user.first_name}!")
    await message.answer(
        descriptions[0],
        reply_markup=like_keyboard(0)
    )

# ===== ЛАЙК =====
@dp.callback_query_handler(lambda c: c.data.startswith("like_"))
async def like_handler(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[1])
    user = callback.from_user

    # Сохраняем лайк для конкретного пользователя
    cursor.execute(
        "INSERT INTO reactions (user_id, username, description, reaction) VALUES (?, ?, ?, ?)",
        (user.id, user.username, descriptions[index], "like")
    )
    conn.commit()

    next_index = index + 1
    if next_index < len(descriptions):
        await callback.message.answer(
            descriptions[next_index],
            reply_markup=like_keyboard(next_index)
        )
    else:
        await callback.message.answer("Это всё 🙂")

    await callback.answer("Лайк сохранён ❤️")

# ===== ДИЗЛАЙК =====
@dp.callback_query_handler(lambda c: c.data.startswith("dislike_"))
async def dislike_handler(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[1])
    next_index = index + 1
    if next_index < len(descriptions):
        await callback.message.answer(
            descriptions[next_index],
            reply_markup=like_keyboard(next_index)
        )
    else:
        await callback.message.answer("Это всё 🙂")

    await callback.answer("Окей 👌")

# ===== АДМИН: ПОСМОТРЕТЬ ЛАЙКИ ПОЛЬЗОВАТЕЛЯ =====
@dp.message_handler(commands=["likes"])
async def show_likes(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    cursor.execute("""
        SELECT user_id, username, description
        FROM reactions
        WHERE reaction='like'
        ORDER BY user_id
    """)
    rows = cursor.fetchall()

    if not rows:
        await message.answer("Лайков пока нет")
        return

    text = "❤️ Лайки пользователей:\n\n"
    last_user = None
    for r in rows:
        if r[0] != last_user:
            text += f"Пользователь: @{r[1]} (id: {r[0]})\n"
            last_user = r[0]
        text += f"→ {r[2]}\n"
    await message.answer(text)

# ===== ЗАПУСК =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
