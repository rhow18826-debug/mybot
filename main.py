import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, InlineQueryHandler, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 7281188442
DB_NAME = "bot_database.db"

# --- دیتابیس برای ذخیره لایک‌ها و ثبت رأی کاربران ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post_likes (
            msg_key TEXT PRIMARY KEY,
            like_count INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_votes (
            click_key TEXT PRIMARY KEY,
            has_liked INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_like_count(msg_key: str, default_val: int = 0) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT like_count FROM post_likes WHERE msg_key = ?", (msg_key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default_val

def set_like_count(msg_key: str, count: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO post_likes (msg_key, like_count) VALUES (?, ?) ON CONFLICT(msg_key) DO UPDATE SET like_count = ?", (msg_key, count, count))
    conn.commit()
    conn.close()

def has_user_voted(click_key: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT has_liked FROM user_votes WHERE click_key = ?", (click_key,))
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row and row[0] == 1 else False

def record_user_vote(click_key: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_votes (click_key, has_liked) VALUES (?, 1) ON CONFLICT(click_key) DO UPDATE SET has_liked = 1", (click_key,))
    conn.commit()
    conn.close()

# --- بررسی عضویت در کانال ---
async def is_user_member(context: ContextTypes.DEFAULT_TYPE, chat_id, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        print(f"Error checking membership: {e}")
        return True
    return False

# --- توابع ربات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guide_text = (
        "👋 به ربات چالش و لایک خوش آمدید!\n\n"
        "📖 راهنمای استفاده از ربات:\n\n"
        "1️⃣ ارسال مستقیم اسم شرکت‌کننده:\n"
        "کافیست در پیوی ربات، اسم شرکت‌کننده را بفرستید تا بنر لایک‌دار برای شما ساخته شود.\n\n"
        "2️⃣ ارسال به کانال توسط ادمین:\n"
        "`/send @channel_id اسم_شرکت‌کننده`"
    )
    await update.message.reply_text(guide_text, parse_mode="Markdown")

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like")]]
    await update.message.reply_text(f"🏆 چالش: {name}", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        channel_id = context.args[0]
        name = " ".join(context.args[1:])
        
        keyboard = [[InlineKeyboardButton("0 ❤️", callback_data="like")]]
        sent_msg = await context.bot.send_message(
            chat_id=channel_id,
            text=f"🏆 چالش: {name}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(
            f"✅ بنر در کانال قرار گرفت!\n🆔 آیدی پیام: `{sent_msg.message_id}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text("❌ فرمت درست:\n`/send @channel_id اسم_شرکت‌کننده`", parse_mode="Markdown")

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # ۱. بررسی عضویت در کانال
    if query.message and query.message.chat:
        chat_id = query.message.chat.id
        if not await is_user_member(context, chat_id, user_id):
            await query.answer("⚠️ برای ثبت لایک باید ابتدا عضو این کانال شوید!", show_alert=True)
            return

    inline_id = query.inline_message_id
    msg_key = inline_id if inline_id else f"{query.message.chat_id}_{query.message.message_id}"
    click_key = f"{msg_key}_{user_id}"

    # ۲. بررسی اینکه آیا کاربر قبلاً لایک زده است یا خیر
    if has_user_voted(click_key):
        await query.answer("⚠️ شما قبلاً به این چالش رای داده‌اید و امکان رای مجدد وجود ندارد!", show_alert=True)
        return

    # ۳. خواندن عدد فعلی لایک
    current_likes = get_like_count(msg_key, 0)

    # افزایش لایک
    new_likes = current_likes + 1
    
    # ثبت رأی کاربر و مقدار جدید لایک در دیتابیس
    record_user_vote(click_key)
    set_like_count(msg_key, new_likes)

    keyboard = [[InlineKeyboardButton(f"{new_likes} ❤️", callback_data="like")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if inline_id:
            await context.bot.edit_message_reply_markup(
                inline_message_id=inline_id,
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_reply_markup(reply_markup=reply_markup)
        await query.answer("❤️ لایک شما با موفقیت ثبت شد!")
    except Exception as e:
        print(f"Error updating markup: {e}")

async def add_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        target = context.args[0]
        
        if len(context.args) == 2 and not target.startswith("@") and not target.startswith("-"):
            inline_id = target
            count = int(context.args[1])
            set_like_count(inline_id, count)
            
            keyboard = [[InlineKeyboardButton(f"{count} ❤️", callback_data="like")]]
            await context.bot.edit_message_reply_markup(
                inline_message_id=inline_id,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await update.message.reply_text(f"✅ لایک به {count} تغییر یافت!")
            return

        chat_id = target
        msg_id = int(context.args[1])
        count = int(context.args[2])

        msg_key = f"{chat_id}_{msg_id}"
        set_like_count(msg_key, count)

        keyboard = [[InlineKeyboardButton(f"{count} ❤️", callback_data="like")]]
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(f"✅ لایک پست به {count} تغییر یافت!")
    except Exception:
        await update.message.reply_text("فرمت صحیح:\n`/addlike @channel_id msg_id 150`", parse_mode="Markdown")

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_post))
    app.add_handler(CommandHandler("addlike", add_likes))
    app.add_handler(CallbackQueryHandler(handle_like))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_name))
    
    app.run_polling()
            
