import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ButtonStyle

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8859541151:AAGx_QDI0b3oL4UmGT8-dqd7l01Knqk6wyY"

# Your Telegram Admin ID
ADMIN_ID = 8289191009

# Channel username or ID
# Example: "@MyChannel"
CHANNEL_ID = "@FreeIncome_TechBD"

# =========================================================
# DATABASE
# =========================================================

db = sqlite3.connect("bot.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS buttons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    text TEXT,
    url TEXT,
    style TEXT DEFAULT 'primary'
)
""")

db.commit()


# =========================================================
# BOT
# =========================================================

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# =========================================================
# STATES
# =========================================================

class PostCreate(StatesGroup):
    waiting_text = State()


class ButtonCreate(StatesGroup):
    waiting_text = State()
    waiting_url = State()
    waiting_style = State()


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id: int):
    return user_id == ADMIN_ID


# =========================================================
# ADMIN MENU
# =========================================================

def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Create Post",
                    callback_data="create_post",
                    style=ButtonStyle.PRIMARY
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔘 Manage Buttons",
                    callback_data="buttons",
                    style=ButtonStyle.SUCCESS
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Publish Post",
                    callback_data="publish",
                    style=ButtonStyle.SUCCESS
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Cancel",
                    callback_data="cancel",
                    style=ButtonStyle.DANGER
                )
            ]
        ]
    )


# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):

    if not is_admin(message.from_user.id):
        await message.answer(
            "👋 Welcome!\n\n"
            "This bot is currently configured for the administrator."
        )
        return

    await message.answer(
        "👑 <b>Admin Post Creator</b>\n\n"
        "Choose an option:",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


# =========================================================
# CREATE POST
# =========================================================

@dp.callback_query(F.data == "create_post")
async def create_post(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        return

    await callback.message.answer(
        "📝 Send the text/caption for your post.\n\n"
        "You can use HTML formatting."
    )

    await state.set_state(PostCreate.waiting_text)

    await callback.answer()


@dp.message(PostCreate.waiting_text)
async def receive_post_text(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    text = message.html_text

    cursor.execute(
        "INSERT INTO posts (text) VALUES (?)",
        (text,)
    )

    db.commit()

    post_id = cursor.lastrowid

    await state.update_data(post_id=post_id)

    await message.answer(
        f"✅ Post created.\n\n"
        f"Post ID: <code>{post_id}</code>\n\n"
        "Now add buttons.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Add Button",
                        callback_data=f"add_button:{post_id}",
                        style=ButtonStyle.SUCCESS
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📢 Publish",
                        callback_data=f"publish:{post_id}",
                        style=ButtonStyle.PRIMARY
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Cancel",
                        callback_data="cancel",
                        style=ButtonStyle.DANGER
                    )
                ]
            ]
        )
    )

    await state.clear()


# =========================================================
# ADD BUTTON
# =========================================================

@dp.callback_query(F.data.startswith("add_button:"))
async def add_button(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        return

    post_id = int(callback.data.split(":")[1])

    await state.update_data(post_id=post_id)

    await callback.message.answer(
        "🔘 Send the button text.\n\n"
        "Example:\n"
        "<code>💰 Buy Now</code>",
        parse_mode="HTML"
    )

    await state.set_state(ButtonCreate.waiting_text)

    await callback.answer()


@dp.message(ButtonCreate.waiting_text)
async def button_text(message: Message, state: FSMContext):

    await state.update_data(button_text=message.text)

    await message.answer(
        "🔗 Now send the button URL.\n\n"
        "Example:\n"
        "https://example.com"
    )

    await state.set_state(ButtonCreate.waiting_url)


# =========================================================
# BUTTON URL
# =========================================================

@dp.message(ButtonCreate.waiting_url)
async def button_url(message: Message, state: FSMContext):

    url = message.text.strip()

    if not (
        url.startswith("https://")
        or url.startswith("http://")
        or url.startswith("tg://")
    ):
        await message.answer(
            "❌ Invalid URL.\n"
            "Please send a valid http://, https:// or tg:// URL."
        )
        return

    await state.update_data(button_url=url)

    await message.answer(
        "🎨 Select button color:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔵 Blue",
                        callback_data="style:primary",
                        style=ButtonStyle.PRIMARY
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🟢 Green",
                        callback_data="style:success",
                        style=ButtonStyle.SUCCESS
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔴 Red",
                        callback_data="style:danger",
                        style=ButtonStyle.DANGER
                    )
                ]
            ]
        )
    )

    await state.set_state(ButtonCreate.waiting_style)


# =========================================================
# BUTTON STYLE
# =========================================================

@dp.callback_query(
    ButtonCreate.waiting_style,
    F.data.startswith("style:")
)
async def button_style(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        return

    style = callback.data.split(":")[1]

    data = await state.get_data()

    post_id = data["post_id"]
    button_text_value = data["button_text"]
    button_url_value = data["button_url"]

    cursor.execute(
        """
        INSERT INTO buttons
        (post_id, text, url, style)
        VALUES (?, ?, ?, ?)
        """,
        (
            post_id,
            button_text_value,
            button_url_value,
            style
        )
    )

    db.commit()

    await state.clear()

    await callback.message.answer(
        "✅ Button added successfully!\n\n"
        f"Text: {button_text_value}\n"
        f"Style: {style}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Add Another Button",
                        callback_data=f"add_button:{post_id}",
                        style=ButtonStyle.SUCCESS
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📢 Publish Now",
                        callback_data=f"publish:{post_id}",
                        style=ButtonStyle.PRIMARY
                    )
                ]
            ]
        )
    )

    await callback.answer()


# =========================================================
# PUBLISH
# =========================================================

@dp.callback_query(F.data.startswith("publish:"))
async def publish(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    post_id = int(callback.data.split(":")[1])

    cursor.execute(
        "SELECT text FROM posts WHERE id=?",
        (post_id,)
    )

    post = cursor.fetchone()

    if not post:
        await callback.answer("Post not found!", show_alert=True)
        return

    text = post[0]

    cursor.execute(
        """
        SELECT text, url, style
        FROM buttons
        WHERE post_id=?
        ORDER BY id ASC
        """,
        (post_id,)
    )

    rows = cursor.fetchall()

    keyboard = []

    for button_text, url, style in rows:

        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                url=url,
                style=style
            )
        ])

    markup = None

    if keyboard:
        markup = InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )

    try:

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            reply_markup=markup,
            parse_mode="HTML"
        )

        await callback.message.answer(
            "✅ <b>Published Successfully!</b>\n\n"
            f"Post ID: <code>{post_id}</code>",
            parse_mode="HTML"
        )

    except Exception as e:

        await callback.message.answer(
            "❌ Publishing failed.\n\n"
            f"<code>{str(e)}</code>",
            parse_mode="HTML"
        )

    await callback.answer()


# =========================================================
# CANCEL
# =========================================================

@dp.callback_query(F.data == "cancel")
async def cancel(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        return

    await state.clear()

    await callback.message.answer(
        "❌ Operation cancelled.",
        reply_markup=admin_menu()
    )

    await callback.answer()


# =========================================================
# BUTTON MANAGEMENT
# =========================================================

@dp.callback_query(F.data == "buttons")
async def manage_buttons(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return

    cursor.execute(
        "SELECT id, text FROM posts ORDER BY id DESC LIMIT 10"
    )

    posts = cursor.fetchall()

    keyboard = []

    for post_id, text in posts:

        preview = text.replace("\n", " ")[:30]

        keyboard.append([
            InlineKeyboardButton(
                text=f"📝 {post_id}: {preview}",
                callback_data=f"publish:{post_id}",
                style=ButtonStyle.PRIMARY
            )
        ])

    if not keyboard:

        await callback.message.answer(
            "No posts available."
        )

    else:

        await callback.message.answer(
            "📋 Your posts:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=keyboard
            )
        )

    await callback.answer()


# =========================================================
# ERROR LOGGING
# =========================================================

@dp.errors()
async def errors_handler(event):
    logging.exception("Telegram error: %s", event.exception)


# =========================================================
# RUN
# =========================================================

async def main():

    logging.basicConfig(
        level=logging.INFO
    )

    print("Bot is starting...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())