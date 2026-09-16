import asyncio
import logging
import os
import sqlite3

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================================================
# CONFIG
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8859541151:AAGx_QDI0b3oL4UmGT8-dqd7l01Knqk6wyY")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@FreeIncome_TechBD)

# তোমার Admin ID
ADMIN_ID = 8289191009

DB_FILE = "bot_database.db"


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# =========================================================
# DATABASE
# =========================================================

db = sqlite3.connect(DB_FILE)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS buttons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    url TEXT NOT NULL,
    style TEXT NOT NULL DEFAULT 'primary'
)
""")

db.commit()


# =========================================================
# BOT / DISPATCHER
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher(storage=MemoryStorage())


# =========================================================
# FSM STATES
# =========================================================

class ButtonStates(StatesGroup):
    waiting_text = State()
    waiting_url = State()
    waiting_style = State()


class PostStates(StatesGroup):
    waiting_text = State()
    waiting_photo = State()


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# =========================================================
# ADMIN MENU
# =========================================================

def admin_menu():

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📝 Create Post",
        callback_data="create_post"
    )

    builder.button(
        text="🔘 Manage Buttons",
        callback_data="manage_buttons"
    )

    builder.button(
        text="📢 Publish Post",
        callback_data="publish_post"
    )

    builder.button(
        text="❌ Cancel",
        callback_data="cancel_all"
    )

    builder.adjust(1)

    return builder.as_markup()


# =========================================================
# /START
# =========================================================

@dp.message(Command("start"))
async def start_handler(message: Message):

    if not is_admin(message.from_user.id):

        await message.answer(
            "⛔ <b>Access Denied</b>\n\n"
            "You are not authorized to use this bot."
        )
        return

    await message.answer(
        "👑 <b>POST CREATOR ADMIN PANEL</b>\n\n"
        "Choose an option:",
        reply_markup=admin_menu()
    )


# =========================================================
# CREATE POST
# =========================================================

@dp.callback_query(F.data == "create_post")
async def create_post(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    await callback.message.answer(
        "📝 <b>Create Post</b>\n\n"
        "Send the text/caption for your post.\n\n"
        "You can use HTML formatting."
    )

    await state.set_state(PostStates.waiting_text)

    await callback.answer()


@dp.message(PostStates.waiting_text)
async def post_text_handler(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    await state.update_data(post_text=message.html_text)

    await message.answer(
        "🖼 <b>Photo is optional.</b>\n\n"
        "Send a photo if you want an image post.\n"
        "Or send /skip to create a text-only post."
    )

    await state.set_state(PostStates.waiting_photo)


@dp.message(PostStates.waiting_photo, Command("skip"))
async def skip_photo(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    await state.update_data(photo_id=None)

    await message.answer(
        "✅ Post saved.\n\n"
        "Now choose <b>Publish Post</b> from the admin panel."
    )

    await state.set_state(None)


@dp.message(PostStates.waiting_photo, F.photo)
async def photo_handler(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    photo_id = message.photo[-1].file_id

    await state.update_data(photo_id=photo_id)

    await message.answer(
        "✅ Photo added.\n\n"
        "Your post is ready."
    )

    await state.set_state(None)


# =========================================================
# ADD BUTTON
# =========================================================

@dp.callback_query(F.data == "manage_buttons")
async def manage_buttons(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    builder = InlineKeyboardBuilder()

    builder.button(
        text="➕ Add Button",
        callback_data="add_button"
    )

    builder.button(
        text="📋 Button List",
        callback_data="button_list"
    )

    builder.button(
        text="🔙 Back",
        callback_data="back_admin"
    )

    builder.adjust(1)

    await callback.message.edit_text(
        "🔘 <b>Button Manager</b>\n\n"
        "Manage your post buttons.",
        reply_markup=builder.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data == "add_button")
async def add_button(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    await callback.message.answer(
        "🔤 Send the button text.\n\n"
        "Example:\n"
        "<code>Join Channel</code>"
    )

    await state.set_state(ButtonStates.waiting_text)

    await callback.answer()


@dp.message(ButtonStates.waiting_text)
async def button_text_handler(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    await state.update_data(button_text=message.text)

    await message.answer(
        "🔗 Now send the button URL.\n\n"
        "Example:\n"
        "<code>https://t.me/example</code>"
    )

    await state.set_state(ButtonStates.waiting_url)


@dp.message(ButtonStates.waiting_url)
async def button_url_handler(message: Message, state: FSMContext):

    if not is_admin(message.from_user.id):
        return

    url = message.text.strip()

    if not (
        url.startswith("https://")
        or url.startswith("http://")
        or url.startswith("tg://")
    ):
        await message.answer(
            "❌ Invalid URL.\n\n"
            "Please send a valid http/https URL."
        )
        return

    await state.update_data(button_url=url)

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔵 Blue",
        callback_data="style_primary"
    )

    builder.button(
        text="🟢 Green",
        callback_data="style_success"
    )

    builder.button(
        text="🔴 Red",
        callback_data="style_danger"
    )

    builder.adjust(1)

    await message.answer(
        "🎨 Choose the button color:",
        reply_markup=builder.as_markup()
    )

    await state.set_state(ButtonStates.waiting_style)


@dp.callback_query(
    ButtonStates.waiting_style,
    F.data.startswith("style_")
)
async def button_style_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    style = callback.data.replace("style_", "")

    data = await state.get_data()

    text = data.get("button_text")
    url = data.get("button_url")

    if not text or not url:
        await callback.message.answer(
            "❌ Button data missing. Please try again."
        )
        await state.clear()
        return

    cursor.execute(
        """
        INSERT INTO buttons (text, url, style)
        VALUES (?, ?, ?)
        """,
        (text, url, style)
    )

    db.commit()

    await state.clear()

    await callback.message.answer(
        "✅ <b>Button Added!</b>\n\n"
        f"Text: {text}\n"
        f"Style: {style}\n"
        f"URL: {url}"
    )

    await callback.answer()


# =========================================================
# BUTTON LIST
# =========================================================

@dp.callback_query(F.data == "button_list")
async def button_list(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    cursor.execute(
        "SELECT id, text, style, url FROM buttons ORDER BY id DESC"
    )

    rows = cursor.fetchall()

    if not rows:

        await callback.message.edit_text(
            "🔘 <b>Button List</b>\n\n"
            "No buttons added yet.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Back",
                            callback_data="manage_buttons"
                        )
                    ]
                ]
            )
        )

        await callback.answer()
        return

    text = "🔘 <b>Button List</b>\n\n"

    for button_id, button_text, style, url in rows:

        text += (
            f"🆔 <b>{button_id}</b>\n"
            f"Text: {button_text}\n"
            f"Style: {style}\n"
            f"URL: {url}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Back",
                        callback_data="manage_buttons"
                    )
                ]
            ]
        )
    )

    await callback.answer()


# =========================================================
# PUBLISH POST
# =========================================================

@dp.callback_query(F.data == "publish_post")
async def publish_post(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    data = await state.get_data()

    post_text = data.get("post_text")
    photo_id = data.get("photo_id")

    if not post_text:

        await callback.message.answer(
            "❌ No post is ready.\n\n"
            "First use <b>Create Post</b>."
        )

        await callback.answer()
        return

    cursor.execute(
        """
        SELECT text, url, style
        FROM buttons
        ORDER BY id ASC
        """
    )

    rows = cursor.fetchall()

    keyboard = []

    for button_text, url, style in rows:

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=button_text,
                    url=url,
                    style=style
                )
            ]
        )

    markup = None

    if keyboard:

        markup = InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )

    try:

        if photo_id:

            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo_id,
                caption=post_text,
                reply_markup=markup
            )

        else:

            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=post_text,
                reply_markup=markup
            )

        await callback.message.answer(
            "✅ <b>Published Successfully!</b>\n\n"
            "Your post has been sent to the channel."
        )

        await state.clear()

    except Exception as e:

        logging.exception("Publish error")

        await callback.message.answer(
            "❌ <b>Publish failed.</b>\n\n"
            f"<code>{str(e)}</code>"
        )

    await callback.answer()


# =========================================================
# CANCEL
# =========================================================

@dp.callback_query(F.data == "cancel_all")
async def cancel_all(callback: CallbackQuery, state: FSMContext):

    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    await state.clear()

    await callback.message.answer(
        "❌ Current operation cancelled."
    )

    await callback.answer()


# =========================================================
# BACK
# =========================================================

@dp.callback_query(F.data == "back_admin")
async def back_admin(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    await callback.message.edit_text(
        "👑 <b>POST CREATOR ADMIN PANEL</b>\n\n"
        "Choose an option:",
        reply_markup=admin_menu()
    )

    await callback.answer()


# =========================================================
# START BOT
# =========================================================

async def main():

    if BOT_TOKEN == "8859541151:AAGx_QDI0b3oL4UmGT8-dqd7l01Knqk6wyY":

        logging.error(
            "BOT_TOKEN is not configured."
        )
        return

    logging.info("Bot is starting...")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logging.info("Bot stopped.")
